"""
Skill assessment API routes — start quizzes, submit answers, view history.
"""
from flask import Blueprint, request, jsonify
from flask import g
from app.utils.auth_helpers import firebase_required
from app import db
from app.models.assessment import Assessment, AssessmentQuestion
from app.services.quiz_service import fetch_quiz_questions

from app.tasks import generate_assessment_questions_task

assessment_bp = Blueprint('assessment', __name__)

@assessment_bp.route('/start', methods=['POST'])
@firebase_required
def start_assessment():
    """Start a new skill assessment quiz supporting multiple skills asynchronously."""
    user_id = g.user_id
    data = request.get_json()
    
    skills = data.get('skills', [])
    if data.get('skill'):
        skills.append(data.get('skill').strip())
        
    skills = list(set([s.strip() for s in skills if s.strip()]))
    count_per_skill = int(data.get('count', 10))
    difficulty = data.get('difficulty', 'medium')

    if not skills:
        return jsonify({'error': 'At least one skill is required.'}), 400

    if len(skills) < 3:
        return jsonify({'error': 'Please select exactly 3 skills for a comprehensive 30-question assessment.'}), 400

    assessment_ids = []
    
    from app.models.taxonomy import SkillTaxonomy
    
    # 1. Synchronously create the Assessments
    for skill_name in skills:
        skill_obj = SkillTaxonomy.query.filter_by(canonical_name=skill_name).first()
        if not skill_obj:
            skill_obj = SkillTaxonomy(canonical_name=skill_name, is_approved=False)
            db.session.add(skill_obj)
            db.session.flush()

        assessment = Assessment(
            user_id=user_id,
            skill_id=skill_obj.id,
            difficulty=difficulty,
            total_questions=count_per_skill,
        )
        db.session.add(assessment)
        db.session.flush()
        assessment_ids.append(assessment.id)

    db.session.commit()

    import threading
    from flask import current_app

    app = current_app._get_current_object()
    def _run_task():
        with app.app_context():
            generate_assessment_questions_task(assessment_ids, skills, count_per_skill, difficulty)
            
    threading.Thread(target=_run_task, daemon=True).start()
    # 3. Return immediately (Lag is eliminated)
    return jsonify({
        'assessment_ids': assessment_ids,
        'skills': skills,
        'difficulty': difficulty,
        'total_questions': len(skills) * count_per_skill,
        'questions': [], # Empty initially, frontend will poll
    }), 201


@assessment_bp.route('/questions', methods=['GET'])
@firebase_required
def get_assessment_questions():
    """Poll for dynamically generated assessment questions."""
    user_id = g.user_id
    ids = request.args.get('ids', '')
    if not ids:
        return jsonify({'error': 'No assessment ids provided'}), 400
        
    assessment_ids = [int(i) for i in ids.split(',') if i.isdigit()]
    
    # Verify ownership
    assessments = Assessment.query.filter(
        Assessment.id.in_(assessment_ids),
        Assessment.user_id == user_id
    ).all()
    
    if not assessments:
        return jsonify({'error': 'Assessments not found or unauthorized'}), 404
        
    valid_ids = [a.id for a in assessments]
    
    # Fetch all questions generated so far
    questions = AssessmentQuestion.query.filter(
        AssessmentQuestion.assessment_id.in_(valid_ids)
    ).all()
    
    q_list = [q.to_dict(include_answer=False) for q in questions]
    
    # Add skill name for UI context
    skill_map = {a.id: (a.skill.canonical_name if a.skill else 'Unknown') for a in assessments}
    for q in q_list:
        q['skill'] = skill_map.get(q['assessment_id'])
        
    # Sort by ID so order is deterministic on frontend
    q_list.sort(key=lambda x: x['id'])

    # Tell the frontend when ALL assessments have their full question sets
    # so it knows to stop polling instead of guessing via settled-state detection.
    all_ready = all(
        AssessmentQuestion.query.filter_by(assessment_id=a.id).count() >= a.total_questions
        for a in assessments
    )

    total_expected = sum(a.total_questions for a in assessments)

    return jsonify({
        'questions': q_list,
        'all_ready': all_ready,
        'total_expected': total_expected
    }), 200


@assessment_bp.route('/submit', methods=['POST'])
@firebase_required
def submit_assessment():
    """Submit answers for multi-skill assessments and get scored results grouped by skill."""
    user_id = g.user_id
    data = request.get_json()
    answers = data.get('answers', {})  # {question_id: "a"|"b"|"c"|"d"}

    if not answers:
        return jsonify({'error': 'No answers provided.'}), 400

    from collections import defaultdict
    from app.models.assessment import Assessment as AssessmentModel
    assessment_scores = defaultdict(lambda: {'correct': 0, 'total': 0})
    results = []

    # Security fix: Join through Assessment to verify ownership — prevents
    # a user from submitting answers for another user's quiz questions
    question_ids = [int(k) for k in answers.keys() if str(k).isdigit()]
    questions = (
        AssessmentQuestion.query
        .join(AssessmentModel, AssessmentModel.id == AssessmentQuestion.assessment_id)
        .filter(
            AssessmentQuestion.id.in_(question_ids),
            AssessmentModel.user_id == user_id   # ownership check
        )
        .all()
    )

    for q in questions:
        user_answer = answers.get(str(q.id))
        is_correct = user_answer == q.correct_answer if user_answer else False
        
        q.user_answer = user_answer
        q.is_correct = is_correct

        assessment_scores[q.assessment_id]['total'] += 1
        if is_correct:
            assessment_scores[q.assessment_id]['correct'] += 1
            
        results.append(q.to_dict(include_answer=True))

    assessment_summary = []
    
    # Update all referenced assessments
    for a_id in assessment_scores.keys():
        assessment = db.session.get(Assessment, a_id)
        if not assessment:
            continue
        
        assessment.score = assessment_scores[a_id]['correct']
        assessment.percentage = round(assessment.score / assessment.total_questions * 100, 1) if assessment.total_questions > 0 else 0
        assessment.passed = assessment.percentage >= 60
        
        if assessment.passed:
            from app.models.user import User, ProfileSkill
            user = db.session.get(User, user_id)
            if user and user.profile:
                # Check if user already has this skill
                existing = ProfileSkill.query.filter_by(
                    profile_id=user.profile.id, 
                    skill_id=assessment.skill_id
                ).first()
                
                if not existing:
                    # Grant skill!
                    ps = ProfileSkill(
                        profile_id=user.profile.id,
                        skill_id=assessment.skill_id,
                        is_desired=False
                    )
                    db.session.add(ps)
                elif existing.is_desired:
                    # Move from "Interested" to "Mastered"
                    existing.is_desired = False
        
        assessment_summary.append({
            'skill': assessment.skill.canonical_name if assessment.skill else "Unknown",
            'score': assessment.score,
            'total': assessment.total_questions,
            'percentage': assessment.percentage,
            'passed': assessment.passed
        })

    db.session.commit()

    return jsonify({
        'summary': assessment_summary,
        'questions': results,
    }), 200


@assessment_bp.route('/history', methods=['GET'])
@firebase_required
def assessment_history():
    """Get user's assessment history."""
    user_id = g.user_id
    assessments = Assessment.query.filter_by(user_id=user_id).order_by(
        Assessment.taken_at.desc()
    ).limit(50).all()
    return jsonify([a.to_dict() for a in assessments]), 200


@assessment_bp.route('/skill-scores', methods=['GET'])
@firebase_required
def skill_scores():
    """Get best score per skill for current user."""
    user_id = g.user_id
    assessments = Assessment.query.filter_by(user_id=user_id).order_by(
        Assessment.taken_at.desc()
    ).all()

    # Best score per skill
    scores = {}
    for a in assessments:
        skill_name = a.skill.canonical_name if a.skill else "Unknown"
        if skill_name not in scores or a.percentage > scores[skill_name]['percentage']:
            scores[skill_name] = {
                'skill': skill_name,
                'percentage': a.percentage,
                'passed': a.passed,
                'taken_at': a.taken_at.isoformat() if a.taken_at else None,
            }

    return jsonify(list(scores.values())), 200
