from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from app import db
from app.models.user import User, Profile
from app.utils.auth_helpers import hash_password, verify_password
import os
import requests as http_requests


def register():
    data = request.get_json()
    email    = (data.get('email') or '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account with this email already exists.'}), 409

    user = User(
        email=email,
        password_hash=hash_password(password),
    )
    db.session.add(user)
    db.session.flush()

    profile = Profile(user_id=user.id)
    db.session.add(profile)
    db.session.commit()

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'message':       'Account created successfully.',
        'access_token':  access_token,
        'refresh_token': refresh_token,
        'user':          user.to_dict(),
    }), 201


def login():
    data = request.get_json()
    email    = (data.get('email') or '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.password_hash:
        return jsonify({'error': 'Invalid email or password.'}), 401

    if not verify_password(password, user.password_hash):
        return jsonify({'error': 'Invalid email or password.'}), 401

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'message':       'Login successful.',
        'access_token':  access_token,
        'refresh_token': refresh_token,
        'user':          user.to_dict(),
    }), 200


def google_login():
    """
    Verify a Google OAuth credential token and create/login the user.
    Expects: { "credential": "<Google ID token>" } from the frontend.
    """
    data = request.get_json()
    credential = data.get('credential', '')

    if not credential:
        return jsonify({'error': 'Google credential token is required.'}), 400

    # Verify token with Google
    google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    try:
        # Use Google's tokeninfo endpoint to verify
        resp = http_requests.get(
            f'https://oauth2.googleapis.com/tokeninfo?id_token={credential}',
            timeout=10
        )
        if resp.status_code != 200:
            return jsonify({'error': 'Invalid Google token.'}), 401

        payload = resp.json()

        # Verify audience matches our client ID
        if google_client_id and payload.get('aud') != google_client_id:
            return jsonify({'error': 'Token audience mismatch.'}), 401

        email = payload.get('email', '').lower()
        google_id = payload.get('sub')
        first_name = payload.get('given_name', '')
        last_name = payload.get('family_name', '')

        if not email:
            return jsonify({'error': 'Could not extract email from Google token.'}), 400

    except Exception as e:
        return jsonify({'error': f'Failed to verify Google token: {str(e)}'}), 401

    # Find or create user
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User.query.filter_by(google_id=google_id).first()

    if not user:
        # Create new user
        user = User(
            email=email,
            google_id=google_id,
            is_verified=True,
        )
        db.session.add(user)
        db.session.flush()

        profile = Profile(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
        )
        db.session.add(profile)
    else:
        # Update google_id if not set
        if not user.google_id:
            user.google_id = google_id
            user.is_verified = True
        
        # Sync name from Google profile
        profile = user.profile
        if not profile:
            profile = Profile(user_id=user.id)
            db.session.add(profile)
            db.session.flush()
        
        # Update name if changed or missing
        profile.first_name = first_name or profile.first_name
        profile.last_name = last_name or profile.last_name

    db.session.commit()

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'message':       'Google login successful.',
        'access_token':  access_token,
        'refresh_token': refresh_token,
        'user':          user.to_dict(),
    }), 200
