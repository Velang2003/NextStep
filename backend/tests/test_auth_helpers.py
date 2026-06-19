"""
Unit tests for app/utils/auth_helpers.py
Tests: hash_password, verify_password
"""
import pytest
from app.utils.auth_helpers import hash_password, verify_password


class TestHashPassword:
    def test_returns_string(self):
        result = hash_password("mysecret123")
        assert isinstance(result, str)

    def test_not_plain_text(self):
        plain = "mysecret123"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_starts_with_bcrypt_prefix(self):
        hashed = hash_password("anypassword")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_unique_hashes(self):
        """Same password hashed twice should produce different salts."""
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        plain = "CorrectHorseBatteryStaple"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("rightpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_password_does_not_crash(self):
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False

    def test_case_sensitive(self):
        hashed = hash_password("Password123")
        assert verify_password("password123", hashed) is False

    def test_roundtrip(self):
        passwords = ["short", "a" * 72, "P@ssw0rd!#", "中文密码"]
        for pwd in passwords:
            h = hash_password(pwd)
            assert verify_password(pwd, h) is True, f"Failed roundtrip for: {pwd}"
