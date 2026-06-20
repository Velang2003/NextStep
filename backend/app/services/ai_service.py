import logging
from app.services.nvidia_service import nvidia_svc

logger = logging.getLogger(__name__)

class AIService:
    """
    Unified AI service — powered by Nvidia NIM (Llama 3.1).
    """
    def __init__(self):
        logger.info("AI Service initialized. Engine: Nvidia NIM.")

    def classify_job(self, title: str, description: str) -> dict:
        from app.services.data_normalizer import classify_department, normalize_role
        return {
            'sector': classify_department(title, description[:500]),
            'role': normalize_role(title),
        }

    def suggest_skills_for_role(self, role_title: str) -> list:
        return nvidia_svc.suggest_skills_for_role(role_title) if hasattr(nvidia_svc, 'suggest_skills_for_role') else []

    def generate_assessment(self, skill_name: str, count: int, difficulty: str) -> list:
        questions = nvidia_svc.generate_assessment(skill_name, count, difficulty)
        if questions:
            return questions
        return []

    def discover_new_entities(self, text: str) -> dict:
        """Identify potential skills and roles using Groq."""
        try:
            res = nvidia_svc.discover_entities(text)
            if res.get('skills') or res.get('role'):
                return res
        except Exception as e:
            logger.warning(f"Nvidia discovery failed: {e}")
        
        # Lightweight fallback using Spacy NER if available
        from app.services.data_normalizer import discover_entities_spacy
        return discover_entities_spacy(text)

# Singleton
ai_svc = AIService()
