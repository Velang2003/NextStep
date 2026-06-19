"""
Unit tests for auth routes — /api/auth/me and /api/auth/sync
Uses Flask test client. Firebase tokens are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client(app):
    return app.test_client()


def _make_decoded_token(uid="firebase_uid_123", email="test@example.com", name="Test User"):
    return {'uid': uid, 'email': email, 'name': name}


class TestGetMeRoute:
    """Tests for GET /api/auth/me"""

    def test_missing_auth_header_returns_401(self, client, app):
        with app.app_context():
            res = client.get('/api/auth/me')
            assert res.status_code == 401
            data = res.get_json()
            assert 'error' in data

    def test_invalid_bearer_token_returns_401(self, client, app):
        with app.app_context():
            with patch('firebase_admin.auth.verify_id_token') as mock_verify:
                mock_verify.side_effect = Exception("Invalid token")
                res = client.get('/api/auth/me', headers={
                    'Authorization': 'Bearer invalid_token_xyz'
                })
            assert res.status_code == 401

    def test_malformed_auth_header_returns_401(self, client, app):
        with app.app_context():
            res = client.get('/api/auth/me', headers={
                'Authorization': 'NotBearer some_token'
            })
            assert res.status_code == 401

    def test_valid_token_returns_user(self, client, session, app):
        with app.app_context():
            decoded = _make_decoded_token(email="auth_me@test.com")
            with patch('firebase_admin.auth.verify_id_token', return_value=decoded):
                res = client.get('/api/auth/me', headers={
                    'Authorization': 'Bearer valid_mock_token'
                })
            assert res.status_code == 200
            data = res.get_json()
            assert 'user' in data
            assert data['user']['email'] == 'auth_me@test.com'

    def test_returns_user_dict_with_email_field(self, client, session, app):
        with app.app_context():
            decoded = _make_decoded_token(email="fields@test.com")
            with patch('firebase_admin.auth.verify_id_token', return_value=decoded):
                res = client.get('/api/auth/me', headers={
                    'Authorization': 'Bearer mock_token'
                })
            data = res.get_json()
            user = data.get('user', {})
            assert 'email' in user


class TestSyncRoute:
    """Tests for POST /api/auth/sync"""

    def test_sync_requires_auth(self, client, app):
        with app.app_context():
            res = client.post('/api/auth/sync')
            assert res.status_code == 401

    def test_sync_with_valid_token(self, client, session, app):
        with app.app_context():
            decoded = _make_decoded_token(email="sync@test.com")
            with patch('firebase_admin.auth.verify_id_token', return_value=decoded):
                res = client.post('/api/auth/sync', headers={
                    'Authorization': 'Bearer mock_sync_token'
                })
            assert res.status_code == 200
            data = res.get_json()
            assert 'message' in data
            assert 'user' in data

    def test_sync_creates_user_in_db(self, client, session, app):
        """First sync should create the user in the local DB."""
        with app.app_context():
            from app.models.user import User
            decoded = _make_decoded_token(
                uid="new_firebase_uid",
                email="newcreated@test.com",
                name="New User"
            )
            with patch('firebase_admin.auth.verify_id_token', return_value=decoded):
                res = client.post('/api/auth/sync', headers={
                    'Authorization': 'Bearer create_me_token'
                })
            assert res.status_code == 200
            user = User.query.filter_by(email='newcreated@test.com').first()
            assert user is not None

    def test_sync_idempotent(self, client, session, app):
        """Calling sync twice with same token should not error."""
        with app.app_context():
            decoded = _make_decoded_token(email="idempotent@test.com")
            with patch('firebase_admin.auth.verify_id_token', return_value=decoded):
                res1 = client.post('/api/auth/sync', headers={
                    'Authorization': 'Bearer token_1'
                })
            with patch('firebase_admin.auth.verify_id_token', return_value=decoded):
                res2 = client.post('/api/auth/sync', headers={
                    'Authorization': 'Bearer token_2'
                })
            assert res1.status_code == 200
            assert res2.status_code == 200


class TestHealthEndpoint:
    """Test the health-check endpoint."""

    def test_health_returns_200(self, client, app):
        with app.app_context():
            res = client.get('/api/health')
            assert res.status_code == 200

    def test_health_response_has_status_key(self, client, app):
        with app.app_context():
            res = client.get('/api/health')
            data = res.get_json()
            assert data.get('status') == 'healthy'
