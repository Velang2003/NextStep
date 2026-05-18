import bcrypt
import time
from datetime import datetime
from functools import wraps
from flask import request, jsonify, g
from firebase_admin import auth as firebase_auth
from app.models.user import User
from app import db

# Allow tokens issued up to 60 seconds "in the future" relative to local clock.
# Needed because the local machine clock may lag behind Firebase servers.
_CLOCK_SKEW_SECONDS = 60


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def _sync_user(decoded_token: dict) -> 'User':
    """
    Look up or create the User record in the local DB from a decoded Firebase token.
    Returns the local User object.
    """
    firebase_uid = decoded_token.get('uid')
    email = decoded_token.get('email')
    name = decoded_token.get('name') or ''

    if not email:
        raise ValueError('Token does not contain an email address.')

    first_name, last_name = '', ''
    if name:
        parts = name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

    user = User.query.filter_by(email=email).first()
    needs_commit = False

    if not user:
        user = User(email=email, google_id=firebase_uid, is_verified=True)
        db.session.add(user)
        db.session.flush()
        from app.models.user import Profile
        db.session.add(Profile(user_id=user.id, first_name=first_name, last_name=last_name))
        needs_commit = True
    else:
        from app.models.user import Profile
        if not user.profile:
            db.session.add(Profile(user_id=user.id, first_name=first_name, last_name=last_name))
            needs_commit = True
        else:
            if not user.profile.first_name and first_name:
                user.profile.first_name = first_name
                needs_commit = True
            if not user.profile.last_name and last_name:
                user.profile.last_name = last_name
                needs_commit = True

    if not user.google_id and firebase_uid:
        user.google_id = firebase_uid
        needs_commit = True

    if needs_commit:
        db.session.commit()

    return user


def firebase_required(f):
    """
    Decorator to verify Firebase ID tokens.
    Uses the built-in clock_skew_seconds parameter (firebase-admin >= 6.0.0)
    to handle local clock drift without blocking the request thread.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token.'}), 401

        id_token = auth_header.split('Bearer ')[1]
        try:
            # clock_skew_seconds tolerates local clock being behind Firebase
            decoded_token = firebase_auth.verify_id_token(
                id_token,
                check_revoked=False,
                clock_skew_seconds=_CLOCK_SKEW_SECONDS
            )
            user = _sync_user(decoded_token)
            g.user_id = user.id
            g.user = user

        except Exception as e:
            import traceback
            with open('crash_dump.log', 'a') as fp:
                fp.write(f"\n--- {datetime.now()} ---\nAuth Error: {str(e)}\n{traceback.format_exc()}\n")
            return jsonify({'error': f'Authentication failed: {str(e)}'}), 401

        return f(*args, **kwargs)

    return decorated_function


def get_firebase_user_id():
    """Helper to get the current user ID from the request context."""
    return getattr(g, 'user_id', None)


def admin_required(f):
    """
    Decorator requiring is_admin=True. Must be applied AFTER @firebase_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = getattr(g, 'user', None)
        if not user:
            return jsonify({'error': 'Authentication required.'}), 401
        if not user.is_admin:
            return jsonify({'error': 'Admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated
