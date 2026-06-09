import os
import json
import logging
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        import threading
        self._lock = threading.Lock()
        
        # Collect keys from both GEMINI_API_KEYS and GEMINI_API_KEY
        raw_keys_list = []
        keys_env = os.getenv('GEMINI_API_KEYS')
        if keys_env:
            raw_keys_list.extend(keys_env.split(','))
        
        single_key = os.getenv('GEMINI_API_KEY')
        if single_key:
            raw_keys_list.append(single_key)
            
        self.api_keys = []
        for key in raw_keys_list:
            clean_key = key.replace('"', '').replace("'", "").strip()
            if clean_key and clean_key not in self.api_keys:
                self.api_keys.append(clean_key)
        
        self.current_key_index = 0
        self.enabled = len(self.api_keys) > 0
        
        if self.enabled:
            self.client = genai.Client(api_key=self.api_keys[self.current_key_index])
            logger.info(f"GeminiService initialized with {len(self.api_keys)} API keys.")
        else:
            self.enabled = False
            logger.warning("No Gemini API keys found. GeminiService disabled.")
        
        self.MODEL_FLASH = 'gemini-2.0-flash'
        self.MODEL_PRO = 'gemini-2.0-flash'
        
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
                self.client = genai.Client(api_key=next_key)
                logger.info(f"Rotated Gemini API Key to index {self.current_key_index}")
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
        if self.failure_count >= 10: # Increased threshold for multiple keys
            self.circuit_open = True
            logger.error("Gemini Circuit Breaker OPENed due to multiple failures.")

    @retry(
        stop=stop_after_attempt(5), # Try up to 5 times (rotating keys each time)
        wait=wait_exponential(multiplier=0.5, min=1, max=5),
        reraise=True
    )
    def _call_gemini(self, prompt, model=None):
        if not self._check_circuit():
            raise Exception("Circuit Breaker is OPEN")
        
        target_model = model or self.MODEL_FLASH
        
        # Keep track of which key we are using for this attempt
        current_key = self.api_keys[self.current_key_index] if self.api_keys else None
        
        try:
            response = self.client.models.generate_content(
                model=target_model,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            self.failure_count = 0 # Reset on success
            return response.text
        except Exception as e:
            self._record_failure()
            logger.warning(f"Gemini API call failed with key index {self.current_key_index}: {e}")
            if current_key:
                self._rotate_key(current_key)
            raise e

    def generate_assessment(self, skill_name: str, count: int, difficulty: str) -> list:
        if not self.enabled:
            return []

        prompt = f"""
        Generate exactly {count} technical multiple-choice questions (MCQs) for: {skill_name}.
        Difficulty: {difficulty}.
        
        Return ONLY a JSON array. Each object MUST have:
        - "question": string
        - "code_snippet": string (or empty)
        - "options": {{"a": "...", "b": "...", "c": "...", "d": "..."}}
        - "correct_answer": "a"|"b"|"c"|"d"
        - "explanation": string
        """
        
        try:
            text = self._call_gemini(prompt, model=self.MODEL_PRO)
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini Assessment error after retries: {e}")
            return []

    def discover_entities(self, text: str) -> dict:
        """Extract potential new skills and roles from a job description."""
        if not self.enabled:
            return {'skills': [], 'roles': []}

        prompt = f"""
        Analyze this job description and extract:
        1. Specialized technical skills (tools, languages, frameworks).
        2. The primary job role title.

        Return ONLY JSON: {{"skills": ["skill1", ...], "role": "title"}}
        
        Text: {text[:2000]}
        """
        try:
            text = self._call_gemini(prompt, model=self.MODEL_FLASH)
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini Discovery error after retries: {e}")
            return {'skills': [], 'roles': []}

gemini_svc = GeminiService()
