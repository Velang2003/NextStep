import os
import json
import logging
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            # Strip quotes and whitespace from key
            clean_key = api_key.replace('"', '').strip()
            self.client = genai.Client(api_key=clean_key)
            self.enabled = True
        else:
            self.enabled = False
            logger.warning("GEMINI_API_KEY not found. GeminiService disabled.")
        
        self.MODEL_FLASH = 'gemini-2.0-flash'
        self.MODEL_PRO = 'gemini-2.0-flash'
        
        self.failure_count = 0
        self.last_failure_time = 0
        self.circuit_open = False

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
        if self.failure_count >= 5:
            self.circuit_open = True
            logger.error("Gemini Circuit Breaker OPENed due to multiple failures.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _call_gemini(self, prompt, model=None):
        if not self._check_circuit():
            raise Exception("Circuit Breaker is OPEN")
        
        target_model = model or self.MODEL_FLASH
        
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
