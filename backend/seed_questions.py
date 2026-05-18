import json
import os
from app import create_app, db
from app.models.assessment import QuestionBank
from app.models.taxonomy import SkillTaxonomy

def seed_questions(json_file='questions.json'):
    if not os.path.exists(json_file):
        print(f"File {json_file} not found!")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    app = create_app()
    with app.app_context():
        inserted = 0
        for q in questions:
            skill_name = q.get('skill')
            skill_obj = SkillTaxonomy.query.filter_by(canonical_name=skill_name).first()
            if not skill_obj:
                print(f"Warning: Skill '{skill_name}' not found in Taxonomy. Auto-creating it...")
                skill_obj = SkillTaxonomy(canonical_name=skill_name, is_approved=True)
                db.session.add(skill_obj)
                db.session.flush()

            # Prevent exact duplicates
            exists = QuestionBank.query.filter_by(skill_id=skill_obj.id, question_text=q['question']).first()
            if not exists:
                new_q = QuestionBank(
                    skill_id=skill_obj.id,
                    difficulty=q.get('difficulty', 'medium'),
                    question_text=q['question'],
                    code_snippet=q.get('code_snippet', ''),
                    options=q.get('options', {}),
                    correct_answer=q.get('correct_answer', 'a').lower(),
                    explanation=q.get('explanation', '')
                )
                db.session.add(new_q)
                inserted += 1

        db.session.commit()
        print(f"Successfully seeded {inserted} new questions into the database!")

if __name__ == '__main__':
    seed_questions()
