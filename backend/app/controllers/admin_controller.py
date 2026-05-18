from flask import Blueprint, jsonify
from app import db
from app.models.taxonomy import SkillTaxonomy

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/pending_skills', methods=['GET'])
def get_pending_skills():
    """Retrieve all skills awaiting admin approval."""
    pending = SkillTaxonomy.query.filter_by(is_approved=False).all()
    return jsonify([p.to_dict() for p in pending]), 200

@admin_bp.route('/approve_skill/<int:skill_id>', methods=['POST'])
def approve_skill(skill_id):
    """Approve a newly discovered skill."""
    skill = db.session.get(SkillTaxonomy, skill_id)
    if not skill:
        return jsonify({'error': 'Skill not found'}), 404
        
    skill.is_approved = True
    db.session.commit()
    return jsonify({'message': f'Skill {skill.canonical_name} approved.'}), 200

@admin_bp.route('/reject_skill/<int:skill_id>', methods=['POST'])
def reject_skill(skill_id):
    """Reject and delete a newly discovered skill."""
    skill = db.session.get(SkillTaxonomy, skill_id)
    if not skill:
        return jsonify({'error': 'Skill not found'}), 404
        
    db.session.delete(skill)
    db.session.commit()
    return jsonify({'message': 'Skill rejected and removed.'}), 200
