"""
Nvidia NIM API Service
Uses OpenAI-compatible endpoint for Nvidia hosted models.
"""
import os
import json
import logging
import time
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class NvidiaService:
    def __init__(self):
        self.api_key = os.getenv('NVIDIA_API_KEY', '')
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            self.client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=self.api_key
            )
            logger.info("NvidiaService initialized.")
        else:
            logger.warning("No NVIDIA_API_KEY found. NvidiaService disabled.")
            
        self.MODEL = 'meta/llama-3.1-8b-instruct'

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True
    )
    def _call_nvidia(self, system_prompt, user_prompt):
        try:
            time.sleep(1) # Polite delay
            
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                # response_format={"type": "json_object"} # Depending on model support
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Nvidia API error: {e}")
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
        - "code_snippet": string (or empty). Only use this for code context (e.g., buggy code to debug, code to evaluate, or a fill-in-the-blank snippet). DO NOT put the correct answer itself inside the code_snippet, as that makes the question trivial. If the question is conceptual (e.g. "How do you do X?"), the code_snippet MUST be empty.
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
            text = self._call_nvidia(system_prompt, user_prompt)
            # Sometimes models return markdown fences around JSON
            if text.startswith("```json"):
                text = text.strip("`").strip("json").strip()
            elif text.startswith("```"):
                text = text.strip("`").strip()
                
            data = json.loads(text)
            if isinstance(data, dict) and "questions" in data:
                return data["questions"]
            elif isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error(f"Nvidia Assessment error: {e}")
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
            text = self._call_nvidia(system_prompt, user_prompt)
            if text.startswith("```json"):
                text = text.strip("`").strip("json").strip()
            elif text.startswith("```"):
                text = text.strip("`").strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Nvidia Discovery error: {e}")
            return {'skills': [], 'roles': []}

nvidia_svc = NvidiaService()
