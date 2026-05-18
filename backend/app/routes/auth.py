from flask import Blueprint, jsonify, g
from app.utils.auth_helpers import firebase_required
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/me', methods=['GET'])
@firebase_required
def get_current_user():
    """
    Returns the current user profile based on the Firebase ID token.
    The firebase_required decorator ensures g.user is populated.
    """
    if not g.user:
        return jsonify({'error': 'User not found in database.'}), 404
    
    return jsonify({
        'user': g.user.to_dict()
    }), 200

@auth_bp.route('/sync', methods=['POST'])
@firebase_required
def sync_user():
    """
    Explicitly sync/confirm user registration from the frontend.
    Useful after a first-time Google sign-in or Email signup.
    The decorator already handles the sync logic.
    """
    return jsonify({
        'message': 'User synced successfully.',
        'user': g.user.to_dict()
    }), 200
