import os
import json
import logging
import threading
import time
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        self._lock = threading.Lock()
        
        # Collect keys
        raw_keys_list = []
        keys_env = os.getenv('GROQ_API_KEYS')
        if keys_env:
            raw_keys_list.extend(keys_env.split(','))
            
        self.api_keys = []
        for key in raw_keys_list:
            clean_key = key.replace('"', '').replace("'", "").strip()
            if clean_key and clean_key not in self.api_keys:
                self.api_keys.append(clean_key)
                
        self.current_key_index = 0
        self.enabled = len(self.api_keys) > 0
        
        if self.enabled:
            self.client = Groq(api_key=self.api_keys[self.current_key_index])
            logger.info(f"GroqService initialized with {len(self.api_keys)} API keys.")
        else:
            self.enabled = False
            logger.warning("No Groq API keys found. GroqService disabled.")
            
        self.MODEL = 'llama-3.1-8b-instant' # Extremely fast open-source model
        
        self.failure_count = 0
        self.last_failure_time = 0
        self.circuit_open = False

    def _rotate_key(self, failed_key):
        """Thread-safe rotation of the API key."""
        with self._lock:
            if not self.api_keys or len(self.api_keys) <= 1:
                return False
            
            # Verify if current key matches failed key to avoid double rotation
            current_key = self.api_keys[self.current_key_index]
            if failed_key == current_key:
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                next_key = self.api_keys[self.current_key_index]
                self.client = Groq(api_key=next_key)
                logger.info(f"Rotated Groq API Key to index {self.current_key_index}")
                return True
            return False

    def _check_circuit(self):
        if self.circuit_open:
            if time.time() - self.last_failure_time > 300: # Reset after 5 mins
                self.circuit_open = False
                self.failure_count = 0
                return True
            return False
        return True

    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= (len(self.api_keys) * 3): # Allow multiple retries per key
            self.circuit_open = True
            logger.error("Groq Circuit Breaker OPENed due to multiple failures. Pipeline will stall for 5 minutes.")

    @retry(
        stop=stop_after_attempt(6), # Try up to 6 times
        wait=wait_exponential(multiplier=2, min=2, max=10), # Start with 2s, 4s, 8s, 10s backoff
        reraise=True
    )
    def _call_groq(self, system_prompt, user_prompt):
        if not self._check_circuit():
            raise Exception("Circuit Breaker is OPEN. Too many API failures.")
            
        current_key = self.api_keys[self.current_key_index] if self.api_keys else None
        
        try:
            # Enforce a baseline delay to stay safely under the ~30 RPM free tier limit.
            # 3.5s = ~17 RPM with two keys, well under the 30 RPM ceiling.
            time.sleep(3.5)
            
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            self.failure_count = 0
            return response.choices[0].message.content
        except Exception as e:
            self._record_failure()
            error_str = str(e).lower()
            logger.warning(f"Groq API call failed with key index {self.current_key_index}: {e}")
            
            # If rate limit hit or auth error, rotate immediately
            if '429' in error_str or 'rate' in error_str or '401' in error_str:
                logger.info("Rate limit or Auth error detected. Rotating keys.")
                if current_key:
                    self._rotate_key(current_key)
            raise e

    def generate_assessment(self, skill_name: str, count: int, difficulty: str) -> list:
        if not self.enabled:
            return []

        system_prompt = "You are an expert technical interviewer. You must output valid JSON."
        user_prompt = f"""
        Generate exactly {count} technical multiple-choice questions (MCQs) for: {skill_name}.
        Difficulty: {difficulty}.
        
        Return ONLY a JSON object with an array named "questions". Each object in the array MUST have:
        - "question": string
        - "code_snippet": string (or empty)
        - "options": {{"a": "...", "b": "...", "c": "...", "d": "..."}}
        - "correct_answer": "a"|"b"|"c"|"d"
        - "explanation": string
        
        Example JSON format:
        {{
            "questions": [
                {{
                    "question": "...",
                    "code_snippet": "...",
                    "options": {{"a": "...", "b": "...", "c": "...", "d": "..."}},
                    "correct_answer": "a",
                    "explanation": "..."
                }}
            ]
        }}
        """
        
        try:
            text = self._call_groq(system_prompt, user_prompt)
            data = json.loads(text)
            # Handle potential wrapping keys like "questions"
            if isinstance(data, dict) and "questions" in data:
                return data["questions"]
            elif isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error(f"Groq Assessment error after retries: {e}")
            return []

    def discover_entities(self, text: str) -> dict:
        """Extract potential new skills and roles from a job description."""
        if not self.enabled:
            return {'skills': [], 'roles': []}

        system_prompt = "You are an expert job market analyst. You must output valid JSON."
        user_prompt = f"""
        Analyze this job description and extract:
        1. Specialized technical skills (tools, languages, frameworks). Do not include soft skills.
        2. The primary job role title (e.g. 'Software Engineer').

        Return ONLY a JSON object exactly like this: {{"skills": ["skill1", ...], "role": "title"}}
        
        Text: {text[:3000]}
        """
        try:
            text = self._call_groq(system_prompt, user_prompt)
            return json.loads(text)
        except Exception as e:
            logger.error(f"Groq Discovery error after retries: {e}")
            return {'skills': [], 'roles': []}

groq_svc = GroqService()
