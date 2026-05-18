import logging
from app.services.gemini_service import gemini_svc

logger = logging.getLogger(__name__)

class AIService:
    """
    Unified AI service — exclusively powered by Google Gemini.
    All local models (Ollama, GGUF) have been removed.
    """
    def __init__(self):
        logger.info("AI Service initialized. Engine: Gemini.")

    def classify_job(self, title: str, description: str) -> dict:
        from app.services.data_normalizer import classify_department, normalize_role
        return {
            'sector': classify_department(title, description[:500]),
            'role': normalize_role(title),
        }

    def suggest_skills_for_role(self, role_title: str) -> list:
        return gemini_svc.suggest_skills_for_role(role_title) if hasattr(gemini_svc, 'suggest_skills_for_role') else []

    def generate_assessment(self, skill_name: str, count: int, difficulty: str) -> list:
        questions = gemini_svc.generate_assessment(skill_name, count, difficulty)
        if questions:
            return questions
        return []

    def discover_new_entities(self, text: str) -> dict:
        """Identify potential skills and roles using Gemini."""
        try:
            res = gemini_svc.discover_entities(text)
            if res.get('skills') or res.get('role'):
                return res
        except Exception as e:
            logger.warning(f"Gemini discovery failed: {e}")
        
        # Lightweight fallback using Spacy NER if available
        from app.services.data_normalizer import discover_entities_spacy
        return discover_entities_spacy(text)

# Singleton
ai_svc = AIService()
