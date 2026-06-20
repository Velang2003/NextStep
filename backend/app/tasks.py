from flask import current_app
from app import db
from app.models.assessment import Assessment, AssessmentQuestion
from app.services.pipeline import run_pipeline as run_pipeline_service
import logging
import random

logger = logging.getLogger(__name__)


def generate_assessment_questions_task(assessment_ids, skills, count_per_skill, difficulty):
    """
    Background task to generate assessment questions.
    Calls Groq directly to generate the full count_per_skill questions per skill in one shot.
    Deduplicates against QuestionBank before saving to AssessmentQuestion.
    """
    from app.models.taxonomy import SkillTaxonomy
    from app.models.assessment import QuestionBank
    from app.services.ai_service import ai_svc

    for a_id, skill_name in zip(assessment_ids, skills):
        try:
            skill_obj = SkillTaxonomy.query.filter_by(canonical_name=skill_name).first()
            if not skill_obj:
                logger.warning(f"Skill '{skill_name}' not found in taxonomy — skipping.")
                continue

            # ── Step 1: Pull existing questions from QuestionBank ──
            cached_qs = QuestionBank.query.filter_by(
                skill_id=skill_obj.id, difficulty=difficulty
            ).all()

            new_bank_items = list(cached_qs)

            # ── Step 2: If we don't have enough, generate the gap via Groq ──
            if len(cached_qs) < count_per_skill:
                needed = count_per_skill - len(cached_qs)
                logger.info(f"[{skill_name}] Generating {needed} new questions via Groq...")
                groq_qs = ai_svc.generate_assessment(skill_name, needed, difficulty)

                for q in groq_qs:
                    if not q.get('question'):
                        continue
                    exists = QuestionBank.query.filter_by(
                        skill_id=skill_obj.id,
                        question_text=q['question']
                    ).first()
                    if not exists:
                        qb = QuestionBank(
                            skill_id=skill_obj.id,
                            question_text=q.get('question', ''),
                            code_snippet=q.get('code_snippet', '') or '',
                            options=q.get('options', {}),
                            correct_answer=str(q.get('correct_answer', 'a'))[:10],
                            explanation=q.get('explanation', '') or '',
                            difficulty=difficulty,
                        )
                        db.session.add(qb)
                        db.session.flush()
                        new_bank_items.append(qb)

                db.session.commit()
                logger.info(f"[{skill_name}] QuestionBank now has {len(new_bank_items)} questions.")

            # ── Step 3: Sample exactly count_per_skill from all available ──
            available = QuestionBank.query.filter_by(skill_id=skill_obj.id).all()
            count_to_use = min(count_per_skill, len(available))
            if count_to_use == 0:
                logger.error(f"[{skill_name}] No questions available after generation!")
                continue

            selected = random.sample(available, count_to_use)

            # ── Step 4: Save deduplicated questions to AssessmentQuestion ──
            for qb in selected:
                aq = AssessmentQuestion(
                    assessment_id=a_id,
                    question_text=qb.question_text,
                    code_snippet=qb.code_snippet or '',
                    options=qb.options,
                    correct_answer=str(qb.correct_answer)[:10],
                    explanation=qb.explanation or '',
                )
                db.session.add(aq)

            # Update total_questions in case we generated fewer than expected
            assessment = Assessment.query.get(a_id)
            if assessment and count_to_use < assessment.total_questions:
                assessment.total_questions = count_to_use

            db.session.commit()
            logger.info(f"[{skill_name}] Saved {count_to_use} AssessmentQuestions for assessment {a_id}.")

        except Exception as e:
            logger.error(f"Assessment generation error for skill '{skill_name}': {e}")
            import traceback
            traceback.print_exc()
            try:
                db.session.rollback()
                # If it failed, cap the total_questions to whatever exists
                assessment = Assessment.query.get(a_id)
                if assessment:
                    actual_count = AssessmentQuestion.query.filter_by(assessment_id=a_id).count()
                    assessment.total_questions = actual_count
                    db.session.commit()
            except Exception:
                pass

    # ── Background bank top-up: fill each skill to 50 questions asynchronously ──
    from app.services.quiz_service import populate_question_bank
    for skill_name in skills:
        populate_question_bank(skill_name, difficulty=difficulty, target_count=50)
