from flask import current_app
from app import db
from app.models.assessment import Assessment, AssessmentQuestion
from app.services.quiz_service import fetch_quiz_questions
from app.services.pipeline import run_pipeline as run_pipeline_service
import logging

logger = logging.getLogger(__name__)

def generate_assessment_questions_task(assessment_ids, skills, count_per_skill, difficulty):
    """
    Background task to generate assessment questions.
    """
    for a_id, skill_name in zip(assessment_ids, skills):
        try:
            # 1. Fetch the first batch (e.g. 3 questions) for instant gratification
            first_batch_count = min(3, count_per_skill)
            first_q_list = fetch_quiz_questions(skill_name, count=first_batch_count, difficulty=difficulty)
            
            for q in first_q_list:
                aq = AssessmentQuestion(
                    assessment_id=a_id,
                    question_text=q.get('question', 'Missing Question'),
                    code_snippet=q.get('code_snippet', '') or '',
                    options=q.get('options', {}),
                    correct_answer=str(q.get('correct_answer', 'a'))[:10],
                    explanation=q.get('explanation', '') or '',
                )
                db.session.add(aq)
            db.session.commit()

            # 2. Fetch the remaining questions needed for this user's assessment
            remaining_needed = count_per_skill - first_batch_count
            if remaining_needed > 0:
                remaining_qs = fetch_quiz_questions(skill_name, count=remaining_needed, difficulty=difficulty)
                for q in remaining_qs:
                    aq = AssessmentQuestion(
                        assessment_id=a_id,
                        question_text=q.get('question', 'Missing Question'),
                        code_snippet=q.get('code_snippet', '') or '',
                        options=q.get('options', {}),
                        correct_answer=str(q.get('correct_answer', 'a'))[:10],
                        explanation=q.get('explanation', '') or '',
                    )
                    db.session.add(aq)
                db.session.commit()
        except Exception as e:
            logger.error(f"[Celery Task] Assessment Generation Error: Skill {skill_name}, Error: {e}")
            db.session.rollback()
            
    # 3. Finally, safely populate the database up to 50 questions for each skill sequentially 
    # to avoid overlapping SQLAlchemy context errors.
    from app.services.quiz_service import populate_question_bank
    for skill_name in skills:
        populate_question_bank(skill_name, difficulty=difficulty, target_count=50)
