"""
Quiz service — fetches MCQ questions from the QuestionBank (DB cache)
with on-demand Gemini generation only when the bank is empty.
"""
from app import db
from typing import Optional


def fetch_combined_quiz(skill_names: list[str], questions_per_skill: int = 10) -> list[dict]:
    """
    Fetch questions for multiple skills and combine them.
    Each skill gets `questions_per_skill` MCQs.
    """
    all_questions = []
    for skill in skill_names[:3]: # Cap at 3 skills
        skill_qs = fetch_quiz_questions(skill, count=questions_per_skill)
        for q in skill_qs:
            q['skill'] = skill
        all_questions.extend(skill_qs)
    
    import random
    random.shuffle(all_questions)
    return all_questions


def fetch_quiz_questions(skill_name: str, count: int = 10,
                         difficulty: Optional[str] = None) -> list[dict]:
    """
    Fetch MCQ questions for a skill.
    Priority: QuestionBank DB (any difficulty) > Gemini API > System Notice fallback.
    """
    from app.models.assessment import QuestionBank
    from app.models.taxonomy import SkillTaxonomy
    import random
    
    skill_obj = SkillTaxonomy.query.filter_by(canonical_name=skill_name).first()
    if not skill_obj:
        return []

    difficulty_val = difficulty or 'medium'
    
    # ── Step 1: Try exact difficulty match from QuestionBank ──
    cached_qs = QuestionBank.query.filter_by(
        skill_id=skill_obj.id, difficulty=difficulty_val
    ).all()
    
    # ── Step 2: If not enough, relax difficulty and use ANY questions for this skill ──
    if len(cached_qs) < count:
        all_skill_qs = QuestionBank.query.filter_by(skill_id=skill_obj.id).all()
        if len(all_skill_qs) >= count:
            cached_qs = all_skill_qs
    
    # ── Step 3: If DB has enough, serve from DB directly (zero API calls) ──
    if len(cached_qs) >= count:
        selected = random.sample(cached_qs, count)
        return [q.to_dict() for q in selected]
    
    # ── Step 4: DB doesn't have enough — generate via Groq ──
    needed = min(count, 10)   # Cap at 10 per single call to keep prompts manageable
    
    try:
        from app.services.ai_service import ai_svc
        new_qs = ai_svc.generate_assessment(skill_name, needed, difficulty_val)
        
        if not new_qs:
            raise Exception("Groq returned no questions (Quota Exhausted / Circuit Breaker)")
            
        for q in new_qs:
            exists = QuestionBank.query.filter_by(
                skill_id=skill_obj.id, question_text=q.get('question', '')
            ).first()
            if not exists and q.get('question'):
                db.session.add(QuestionBank(
                    skill_id=skill_obj.id,
                    question_text=q.get('question', ''),
                    code_snippet=q.get('code_snippet', ''),
                    options=q.get('options', {}),
                    correct_answer=str(q.get('correct_answer', 'a'))[:10],
                    explanation=q.get('explanation', ''),
                    difficulty=difficulty_val
                ))
        db.session.commit()
        
        # Re-query and return
        cached_qs = QuestionBank.query.filter_by(skill_id=skill_obj.id).all()
        selected = random.sample(cached_qs, min(count, len(cached_qs)))
        return [q.to_dict() for q in selected]
        
    except Exception as e:
        db.session.rollback()
        print(f"[Quiz Service Error]: {e}")
        
        # If we have ANY questions at all from the earlier query, use them
        if cached_qs:
            selected = random.sample(cached_qs, min(count, len(cached_qs)))
            return [q.to_dict() for q in selected]
        
        # Last resort: return a system notice so the UI doesn't hang forever
        return [{
            'question': f"System Notice: Could not generate questions for {skill_name}. Please check Gemini API Quota.",
            'options': {'a': 'Acknowledge', 'b': 'Retry Later', 'c': 'Check Billing', 'd': 'Contact Admin'},
            'correct_answer': 'a',
            'explanation': str(e)[:200],
            'skill': skill_name
        }]


def populate_question_bank(skill_name: str, difficulty: str = 'medium', target_count: int = 50):
    """
    Sequentially populates the question bank up to the target count.
    Designed to be called from an existing background thread.
    """
    from app.models.assessment import QuestionBank
    from app.models.taxonomy import SkillTaxonomy
    
    skill_obj = SkillTaxonomy.query.filter_by(canonical_name=skill_name).first()
    if not skill_obj:
        return
        
    try:
        current_count = QuestionBank.query.filter_by(skill_id=skill_obj.id).count()
        if current_count >= target_count:
            return
            
        fetch_amount = min(target_count - current_count, 15)
        from app.services.ai_service import ai_svc
        bg_qs = ai_svc.generate_assessment(skill_name, fetch_amount, difficulty)
        
        for q in bg_qs:
            exists = QuestionBank.query.filter_by(
                skill_id=skill_obj.id, question_text=q.get('question', '')
            ).first()
            if not exists and q.get('question'):
                db.session.add(QuestionBank(
                    skill_id=skill_obj.id,
                    question_text=q.get('question', ''),
                    code_snippet=q.get('code_snippet', ''),
                    options=q.get('options', {}),
                    correct_answer=str(q.get('correct_answer', 'a'))[:10],
                    explanation=q.get('explanation', ''),
                    difficulty=difficulty
                ))
        db.session.commit()
        print(f"[QuestionBank] Populated {len(bg_qs)} background questions for {skill_name}")
    except Exception as e:
        db.session.rollback()
        print(f"[QuestionBank Populate Error]: {e}")
