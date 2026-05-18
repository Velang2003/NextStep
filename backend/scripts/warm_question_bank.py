import os
import sys
from datetime import datetime

# Add the backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.taxonomy import SkillTaxonomy
from app.models.assessment import QuestionBank
from app.services.quiz_service import fetch_quiz_questions
from sqlalchemy import func

def warm_cache():
    app = create_app()
    with app.app_context():
        print(f"[{datetime.now()}] Starting Question Bank Warming...")

        # 1. Identify top 20 approved skills
        top_skills = SkillTaxonomy.query.filter_by(is_approved=True).limit(20).all()
        
        if not top_skills:
            print("No approved skills found to warm.")
            return

        for skill in top_skills:
            print(f"Processing skill: {skill.canonical_name}...")
            
            current_count = QuestionBank.query.filter_by(skill_id=skill.id).count()
            target_count = 50
            
            if current_count < target_count:
                to_generate = target_count - current_count
                print(f"Generating {to_generate} questions for {skill.canonical_name}...")
                
                # Fetch in batches of 10 to avoid timeouts
                batch_size = 10
                for i in range(0, to_generate, batch_size):
                    count = min(batch_size, to_generate - i)
                    try:
                        # Note: fetch_quiz_questions might call Gemini which saves to QuestionBank
                        # But it first checks QuestionBank. 
                        # To force generation, we might need a separate service call 
                        # but generate_assessment is private to GeminiService.
                        
                        from app.services.ai_service import ai_svc
                        questions = ai_svc.generate_assessment(skill.canonical_name, count, "medium")
                        
                        if questions:
                            for q in questions:
                                # Basic deduplication by text
                                exists = QuestionBank.query.filter_by(
                                    skill_id=skill.id, 
                                    question_text=q['question']
                                ).first()
                                if not exists:
                                    db.session.add(QuestionBank(
                                        skill_id=skill.id,
                                        question_text=q['question'],
                                        code_snippet=q.get('code_snippet', ''),
                                        options=q['options'],
                                        correct_answer=q['correct_answer'],
                                        explanation=q.get('explanation', ''),
                                        difficulty='medium'
                                    ))
                            db.session.commit()
                            print(f"  Added {len(questions)} questions.")
                    except Exception as e:
                        print(f"  Error generating batch: {e}")
                        db.session.rollback()
            else:
                print(f"Skill {skill.canonical_name} already has {current_count} questions.")

        print(f"[{datetime.now()}] Question Bank Warming Complete.")

if __name__ == "__main__":
    warm_cache()
