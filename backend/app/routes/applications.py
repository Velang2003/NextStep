from flask import Blueprint, request, jsonify, g
from app.utils.auth_helpers import firebase_required
from app import db
from app.models.application import JobApplication
from app.models.job import JobListing
from datetime import datetime, timezone

applications_bp = Blueprint('applications', __name__)


@applications_bp.route('/', methods=['GET'])
@firebase_required
def list_applications():
    """List all user's tracked job applications."""
    user_id = g.user_id
    status = request.args.get('status')

    query = JobApplication.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)

    apps = query.order_by(JobApplication.updated_at.desc()).all()
    return jsonify([a.to_dict() for a in apps]), 200


@applications_bp.route('/save', methods=['POST'])
@firebase_required
def save_job():
    """Save/bookmark a job listing."""
    user_id = g.user_id
    data = request.get_json()
    job_id = data.get('job_id')

    if not job_id:
        return jsonify({'error': 'job_id is required.'}), 400

    job = db.session.get(JobListing, job_id)
    if not job:
        return jsonify({'error': 'Job not found.'}), 404

    existing = JobApplication.query.filter_by(user_id=user_id, job_id=job_id).first()
    if existing:
        return jsonify({'message': 'Already tracked.', 'application': existing.to_dict()}), 200

    app = JobApplication(
        user_id=user_id,
        job_id=job_id,
        status='saved',
    )
    db.session.add(app)
    db.session.commit()

    return jsonify({'message': 'Job saved.', 'application': app.to_dict()}), 201


@applications_bp.route('/apply', methods=['POST'])
@firebase_required
def apply_to_job():
    """Track a job application (auto-saves with 'applied' status)."""
    user_id = g.user_id
    data = request.get_json()
    job_id = data.get('job_id')

    if not job_id:
        return jsonify({'error': 'job_id is required.'}), 400

    job = db.session.get(JobListing, job_id)
    if not job:
        return jsonify({'error': 'Job not found.'}), 404

    existing = JobApplication.query.filter_by(user_id=user_id, job_id=job_id).first()
    if existing:
        existing.status = 'applied'
        existing.applied_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({
            'message': 'Application tracked.',
            'application': existing.to_dict(),
            'url': job.url,
        }), 200

    app = JobApplication(
        user_id=user_id,
        job_id=job_id,
        status='applied',
        applied_at=datetime.now(timezone.utc),
    )
    db.session.add(app)
    db.session.commit()

    return jsonify({
        'message': 'Application tracked.',
        'application': app.to_dict(),
        'url': job.url,
    }), 201


@applications_bp.route('/<int:app_id>/status', methods=['PUT'])
@firebase_required
def update_status(app_id):
    """Update application status (for Kanban board drag-and-drop)."""
    user_id = g.user_id
    data = request.get_json()
    new_status = data.get('status')

    valid_statuses = ['saved', 'applied', 'interviewing', 'offered', 'rejected']
    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    app = JobApplication.query.filter_by(id=app_id, user_id=user_id).first()
    if not app:
        return jsonify({'error': 'Application not found.'}), 404

    app.status = new_status
    if new_status == 'applied' and not app.applied_at:
        app.applied_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({'message': 'Status updated.', 'application': app.to_dict()}), 200


@applications_bp.route('/<int:app_id>/notes', methods=['PUT'])
@firebase_required
def update_notes(app_id):
    """Update notes on an application."""
    user_id = g.user_id
    data = request.get_json()

    app = JobApplication.query.filter_by(id=app_id, user_id=user_id).first()
    if not app:
        return jsonify({'error': 'Application not found.'}), 404

    app.notes = data.get('notes', '')
    db.session.commit()

    return jsonify({'message': 'Notes updated.', 'application': app.to_dict()}), 200


@applications_bp.route('/<int:app_id>', methods=['DELETE'])
@firebase_required
def delete_application(app_id):
    """Remove a tracked application."""
    user_id = g.user_id

    app = JobApplication.query.filter_by(id=app_id, user_id=user_id).first()
    if not app:
        return jsonify({'error': 'Application not found.'}), 404

    db.session.delete(app)
    db.session.commit()

    return jsonify({'message': 'Application removed.'}), 200


@applications_bp.route('/stats', methods=['GET'])
@firebase_required
def application_stats():
    """Get application tracking statistics."""
    user_id = g.user_id
    apps = JobApplication.query.filter_by(user_id=user_id).all()

    stats = {
        'total': len(apps),
        'saved': sum(1 for a in apps if a.status == 'saved'),
        'applied': sum(1 for a in apps if a.status == 'applied'),
        'interviewing': sum(1 for a in apps if a.status == 'interviewing'),
        'offered': sum(1 for a in apps if a.status == 'offered'),
        'rejected': sum(1 for a in apps if a.status == 'rejected'),
    }
    return jsonify(stats), 200
