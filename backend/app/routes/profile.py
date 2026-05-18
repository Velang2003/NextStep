from flask import Blueprint
from app.utils.auth_helpers import firebase_required
from app.controllers.profile_controller import (
    update_profile, get_skill_gap, get_career_path, get_recommended_roles
)

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/', methods=['PUT'])
@firebase_required
def update():
    return update_profile()


@profile_bp.route('/skill-gap', methods=['GET'])
@firebase_required
def skill_gap():
    return get_skill_gap()


@profile_bp.route('/career-path', methods=['GET'])
@firebase_required
def career_path():
    return get_career_path()


@profile_bp.route('/recommended-roles', methods=['GET'])
@firebase_required
def recommended_roles():
    return get_recommended_roles()
