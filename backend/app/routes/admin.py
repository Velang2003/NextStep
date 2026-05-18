"""
Admin Routes — /api/admin/*
Requires Firebase authentication + is_admin=True on the User record.

Endpoints:
  GET    /api/admin/pending-skills          — list pending skill submissions
  POST   /api/admin/pending-skills/:id/approve — approve → insert into skill_taxonomy + optional RoleSkill link
  POST   /api/admin/pending-skills/:id/reject  — reject with optional note
  DELETE /api/admin/pending-skills/:id         — permanently delete a queued item

  GET    /api/admin/taxonomy/roles          — full roles list with aliases & skills
  PUT    /api/admin/taxonomy/roles/:id      — update role title / aliases / sector
  GET    /api/admin/taxonomy/skills         — full skills list with aliases
  PUT    /api/admin/taxonomy/skills/:id     — update skill canonical name / category / aliases

  GET    /api/admin/users                   — list users (id, email, is_admin)
  PATCH  /api/admin/users/:id/toggle-admin  — grant or revoke admin rights
"""

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g
from app import db
from app.models.taxonomy import (
    SkillTaxonomy, SkillAlias,
    RoleTaxonomy, RoleAlias,
    SectorTaxonomy,
    RoleSkill,
    PendingSkill,
    PendingRole,
)
from app.models.user import User
from sqlalchemy import func
from app.utils.auth_helpers import firebase_required, admin_required

admin_bp = Blueprint('admin', __name__)


# ─────────────────────────────────────────────────────────────
# PENDING SKILL QUEUE
# ─────────────────────────────────────────────────────────────

@admin_bp.route('/pending-skills', methods=['GET'])
@firebase_required
@admin_required
def list_pending_skills():
    """Return all skills in the review queue, with optional status filter."""
    status = request.args.get('status', 'pending')   # pending | approved | rejected | all
    query = PendingSkill.query
    if status != 'all':
        query = query.filter_by(status=status)
    items = query.order_by(PendingSkill.submitted_at.desc()).all()
    return jsonify({'pending_skills': [p.to_dict() for p in items], 'total': len(items)}), 200


@admin_bp.route('/pending-skills/<int:skill_id>/approve', methods=['POST'])
@firebase_required
@admin_required
def approve_pending_skill(skill_id):
    """
    Approve a pending skill:
    - Creates a new SkillTaxonomy record (if it doesn't already exist)
    - Optionally links it to a role via RoleSkill
    - Accepts optional JSON body: { category, role_id, aliases: [] }
    """
    pending = PendingSkill.query.get_or_404(skill_id)
    body = request.get_json(silent=True) or {}

    category   = body.get('category') or pending.suggested_category or 'Tool'
    role_id    = body.get('role_id')  or pending.suggested_role_id
    aliases    = body.get('aliases', [])  # list of strings

    # Prevent duplicate
    existing = SkillTaxonomy.query.filter(
        func.lower(SkillTaxonomy.canonical_name) == pending.name.lower()
    ).first()

    if existing:
        skill = existing
        msg = 'Skill already existed — linked only.'
    else:
        skill = SkillTaxonomy(
            canonical_name=pending.name,
            category=category,
            is_approved=True,
        )
        db.session.add(skill)
        db.session.flush()
        msg = 'Skill created and approved.'

    # Add aliases (unique, lower-case)
    for alias_name in aliases:
        alias_clean = alias_name.strip().lower()
        if alias_clean and not SkillAlias.query.filter_by(name=alias_clean).first():
            db.session.add(SkillAlias(name=alias_clean, skill_id=skill.id))

    # Link to role
    if role_id:
        exists_link = RoleSkill.query.filter_by(role_id=role_id, skill_id=skill.id).first()
        if not exists_link:
            db.session.add(RoleSkill(role_id=role_id, skill_id=skill.id))

    pending.status      = 'approved'
    pending.reviewed_at = datetime.now(timezone.utc)
    pending.reviewed_by = g.user.email

    db.session.commit()
    return jsonify({'message': msg, 'skill': skill.to_dict()}), 200


@admin_bp.route('/pending-skills/<int:skill_id>/reject', methods=['POST'])
@firebase_required
@admin_required
def reject_pending_skill(skill_id):
    """Reject a pending skill with an optional admin note."""
    pending = PendingSkill.query.get_or_404(skill_id)
    body = request.get_json(silent=True) or {}

    pending.status      = 'rejected'
    pending.admin_note  = body.get('note', '')
    pending.reviewed_at = datetime.now(timezone.utc)
    pending.reviewed_by = g.user.email

    db.session.commit()
    return jsonify({'message': 'Skill rejected.', 'id': skill_id}), 200


@admin_bp.route('/pending-skills/<int:skill_id>', methods=['DELETE'])
@firebase_required
@admin_required
def delete_pending_skill(skill_id):
    """Permanently remove an entry from the pending queue."""
    pending = PendingSkill.query.get_or_404(skill_id)
    db.session.delete(pending)
    db.session.commit()
    return jsonify({'message': 'Deleted.'}), 200


# ─────────────────────────────────────────────────────────────
# PENDING ROLE QUEUE
# ─────────────────────────────────────────────────────────────

@admin_bp.route('/pending-roles', methods=['GET'])
@firebase_required
@admin_required
def list_pending_roles():
    """Return all roles in the review queue."""
    status = request.args.get('status', 'pending')
    query = PendingRole.query
    if status != 'all':
        query = query.filter_by(status=status)
    items = query.order_by(PendingRole.submitted_at.desc()).all()
    return jsonify({'pending_roles': [r.to_dict() for r in items], 'total': len(items)}), 200


@admin_bp.route('/pending-roles/<int:role_id>/approve', methods=['POST'])
@firebase_required
@admin_required
def approve_pending_role(role_id):
    """
    Approve a pending role:
    - Creates a new RoleTaxonomy record
    - Optionally creates a Sector if it doesn't exist
    """
    pending = PendingRole.query.get_or_404(role_id)
    body = request.get_json(silent=True) or {}

    sector_name = body.get('sector') or pending.suggested_sector or 'Other'
    
    # 1. Ensure Sector exists
    sector = SectorTaxonomy.query.filter(func.lower(SectorTaxonomy.name) == sector_name.lower()).first()
    if not sector:
        sector = SectorTaxonomy(name=sector_name)
        db.session.add(sector)
        db.session.flush()

    # 2. Create Role
    new_role = RoleTaxonomy(
        title=pending.title,
        sector_id=sector.id,
        seniority=body.get('seniority', 'Mid')
    )
    db.session.add(new_role)
    
    pending.status = 'approved'
    pending.reviewed_at = datetime.now(timezone.utc)
    pending.reviewed_by = g.user.email

    db.session.commit()
    return jsonify({'message': 'Role approved and created.', 'role': new_role.to_dict()}), 200


@admin_bp.route('/pending-roles/<int:role_id>/reject', methods=['POST'])
@firebase_required
@admin_required
def reject_pending_role(role_id):
    pending = PendingRole.query.get_or_404(role_id)
    body = request.get_json(silent=True) or {}
    pending.status = 'rejected'
    pending.admin_note = body.get('note', '')
    pending.reviewed_at = datetime.now(timezone.utc)
    pending.reviewed_by = g.user.email
    db.session.commit()
    return jsonify({'message': 'Role rejected.'}), 200


# ─────────────────────────────────────────────────────────────
# TAXONOMY MANAGEMENT — ROLES
# ─────────────────────────────────────────────────────────────

@admin_bp.route('/taxonomy/roles', methods=['POST'])
@firebase_required
@admin_required
def create_role():
    """Manually create a new role."""
    body = request.get_json(silent=True) or {}
    title = body.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400
        
    sector_id = body.get('sector_id')
    
    # Check if exists
    if RoleTaxonomy.query.filter(func.lower(RoleTaxonomy.title) == title.lower().strip()).first():
        return jsonify({'error': 'Role already exists'}), 409
        
    role = RoleTaxonomy(
        title=title.strip(),
        sector_id=sector_id,
        seniority=body.get('seniority', 'Mid')
    )
    db.session.add(role)
    db.session.commit()
    return jsonify({'message': 'Role created.', 'role': role.to_dict()}), 201

@admin_bp.route('/taxonomy/roles', methods=['GET'])
@firebase_required
@admin_required
def list_admin_roles():
    """Full role list with aliases, sector, and skill count."""
    roles = RoleTaxonomy.query.order_by(RoleTaxonomy.title).all()
    data = []
    for r in roles:
        d = r.to_dict()
        d['skill_count'] = RoleSkill.query.filter_by(role_id=r.id).count()
        data.append(d)
    return jsonify({'roles': data, 'total': len(data)}), 200


@admin_bp.route('/taxonomy/roles/<int:role_id>', methods=['PUT'])
@firebase_required
@admin_required
def update_role(role_id):
    """
    Update a role's title, sector, seniority, or aliases.
    Body: { title, sector_id, seniority, aliases: ["exact match phrase", ...] }
    
    Alias design rule: aliases must be UNIQUE and SPECIFIC — no generic
    words like 'developer' that would match multiple roles.
    """
    role = RoleTaxonomy.query.get_or_404(role_id)
    body = request.get_json(silent=True) or {}

    if 'title' in body:
        role.title = body['title'].strip()
    if 'sector_id' in body:
        role.sector_id = body['sector_id']
    if 'seniority' in body:
        role.seniority = body['seniority']

    if 'aliases' in body:
        raw_aliases = body['aliases']
        if isinstance(raw_aliases, str):
            raw_aliases = [raw_aliases]
        new_aliases = [a.strip().lower() for a in raw_aliases if a.strip()]
        
        # Validate uniqueness: no alias should already belong to a DIFFERENT role
        conflicts = []
        for alias_name in new_aliases:
            existing = RoleAlias.query.filter(func.lower(RoleAlias.name) == alias_name).first()
            if existing and existing.role_id != role_id:
                conflicts.append(
                    f"'{alias_name}' already belongs to role '{existing.role.title}'"
                )
        if conflicts:
            return jsonify({'error': 'Alias conflicts detected', 'conflicts': conflicts}), 409

        # Clear and re-set aliases
        RoleAlias.query.filter_by(role_id=role_id).delete()
        for alias_name in new_aliases:
            db.session.add(RoleAlias(name=alias_name, role_id=role_id))

    db.session.commit()
    return jsonify({'message': 'Role updated.', 'role': role.to_dict()}), 200


@admin_bp.route('/taxonomy/roles/<int:role_id>', methods=['DELETE'])
@firebase_required
@admin_required
def delete_role(role_id):
    """Permanently remove a role and its aliases."""
    role = RoleTaxonomy.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    return jsonify({'message': f'Role "{role.title}" deleted.'}), 200


# ─────────────────────────────────────────────────────────────
# TAXONOMY MANAGEMENT — SKILLS
# ─────────────────────────────────────────────────────────────

@admin_bp.route('/taxonomy/skills', methods=['POST'])
@firebase_required
@admin_required
def create_skill():
    """Manually create a new skill."""
    body = request.get_json(silent=True) or {}
    name = body.get('canonical_name')
    if not name:
        return jsonify({'error': 'Canonical name is required'}), 400
        
    if SkillTaxonomy.query.filter(func.lower(SkillTaxonomy.canonical_name) == name.lower().strip()).first():
        return jsonify({'error': 'Skill already exists'}), 409
        
    skill = SkillTaxonomy(
        canonical_name=name.strip(),
        category=body.get('category', 'Tool'),
        is_approved=True
    )
    db.session.add(skill)
    db.session.commit()
    return jsonify({'message': 'Skill created.', 'skill': skill.to_dict()}), 201

@admin_bp.route('/taxonomy/skills', methods=['GET'])
@firebase_required
@admin_required
def list_admin_skills():
    """Full skill list with aliases and category."""
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))

    query = SkillTaxonomy.query
    if search:
        query = query.filter(SkillTaxonomy.canonical_name.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)

    query = query.order_by(SkillTaxonomy.category, SkillTaxonomy.canonical_name)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'skills': [s.to_dict() for s in paginated.items],
        'total':  paginated.total,
        'page':   page,
        'pages':  paginated.pages,
    }), 200


@admin_bp.route('/taxonomy/skills/<int:skill_id>', methods=['PUT'])
@firebase_required
@admin_required
def update_skill(skill_id):
    """
    Update a skill's canonical name, category, or aliases.
    Body: { canonical_name, category, aliases: ["react.js", "reactjs", ...] }

    Alias design rule: aliases must be UNIQUE across ALL skills.
    e.g. 'js' should not alias both 'JavaScript' and 'TypeScript'.
    """
    skill = SkillTaxonomy.query.get_or_404(skill_id)
    body = request.get_json(silent=True) or {}

    if 'canonical_name' in body:
        skill.canonical_name = body['canonical_name'].strip()
    if 'category' in body:
        skill.category = body['category'].strip()

    if 'aliases' in body:
        raw_aliases = body['aliases']
        if isinstance(raw_aliases, str):
            raw_aliases = [raw_aliases]
        new_aliases = [a.strip().lower() for a in raw_aliases if a.strip()]

        # Conflict check — alias must not belong to a different skill
        conflicts = []
        for alias_name in new_aliases:
            existing = SkillAlias.query.filter(func.lower(SkillAlias.name) == alias_name).first()
            if existing and existing.skill_id != skill_id:
                conflicts.append(
                    f"'{alias_name}' already aliases skill '{existing.skill.canonical_name}'"
                )
        if conflicts:
            return jsonify({'error': 'Alias conflicts detected', 'conflicts': conflicts}), 409

        SkillAlias.query.filter_by(skill_id=skill_id).delete()
        for alias_name in new_aliases:
            db.session.add(SkillAlias(name=alias_name, skill_id=skill_id))

    db.session.commit()
    return jsonify({'message': 'Skill updated.', 'skill': skill.to_dict()}), 200


@admin_bp.route('/taxonomy/skills/<int:skill_id>', methods=['DELETE'])
@firebase_required
@admin_required
def delete_skill(skill_id):
    """Permanently remove a skill and its aliases."""
    skill = SkillTaxonomy.query.get_or_404(skill_id)
    db.session.delete(skill)
    db.session.commit()
    return jsonify({'message': f'Skill "{skill.canonical_name}" deleted.'}), 200


# ─────────────────────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_bp.route('/users', methods=['GET'])
@firebase_required
@admin_required
def list_users():
    """List all registered users with basic info."""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    paginated = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        'users': [u.to_dict() for u in paginated.items],
        'total': paginated.total,
        'page':  page,
        'pages': paginated.pages,
    }), 200


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['PATCH'])
@firebase_required
@admin_required
def toggle_admin(user_id):
    """Grant or revoke admin rights for a user."""
    if g.user.id == user_id:
        return jsonify({'error': 'Cannot change your own admin status.'}), 400
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({
        'message': f"Admin {'granted' if user.is_admin else 'revoked'} for {user.email}",
        'is_admin': user.is_admin,
    }), 200


# ─────────────────────────────────────────────────────────────
# STATS DASHBOARD
# ─────────────────────────────────────────────────────────────

@admin_bp.route('/stats', methods=['GET'])
@firebase_required
@admin_required
def admin_stats():
    """Quick overview for the admin dashboard."""
    from app.models.job import JobListing
    return jsonify({
        'total_skills':         SkillTaxonomy.query.count(),
        'total_roles':          RoleTaxonomy.query.count(),
        'total_sectors':        SectorTaxonomy.query.count(),
        'total_role_skill_links': RoleSkill.query.count(),
        'pending_skills':       PendingSkill.query.filter_by(status='pending').count(),
        'pending_roles':        PendingRole.query.filter_by(status='pending').count(),
        'total_jobs':           JobListing.query.count(),
        'active_jobs':          JobListing.query.filter_by(status='active').count(),
        'total_users':          User.query.count(),
        'admin_users':          User.query.filter_by(is_admin=True).count(),
    }), 200

# ─────────────────────────────────────────────────────────────
# PIPELINE MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_bp.route('/pipeline/trigger', methods=['POST'])
@firebase_required
@admin_required
def trigger_pipeline():
    """Trigger the unified job data fetching and processing pipeline in a background thread."""
    from app.services.pipeline import get_pipeline_status, run_pipeline
    import threading

    # Check if already running
    status = get_pipeline_status()
    if status.get('is_running'):
        return jsonify({'message': 'Pipeline is already running.', 'status': status}), 400

    # Run in a background thread (no Celery/Redis dependency)
    from flask import current_app
    app = current_app._get_current_object()

    def _run():
        with app.app_context():
            run_pipeline()

    threading.Thread(target=_run, daemon=True).start()

    return jsonify({
        'message': 'Unified pipeline triggered successfully.',
        'status': 'running'
    }), 200


@admin_bp.route('/pipeline/status', methods=['GET'])
@firebase_required
@admin_required
def pipeline_status_api():
    """Return the current status of the pipeline (step, progress, logs)."""
    from app.services.pipeline import get_pipeline_status
    return jsonify(get_pipeline_status()), 200
