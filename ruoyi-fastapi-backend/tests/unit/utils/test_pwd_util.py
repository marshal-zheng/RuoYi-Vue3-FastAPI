"""
Unit tests for password utility functions.
"""

import pytest
from hypothesis import given, strategies as st

from utils.pwd_util import PwdUtil


class TestPwdUtil:
    """Test suite for password hashing and verification."""

    def test_hash_password_returns_string(self):
        """Test that get_password_hash returns a string."""
        hashed = PwdUtil.get_password_hash('test123')
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Test that hashing same password produces different hashes (salt)."""
        password = 'test123'
        hash1 = PwdUtil.get_password_hash(password)
        hash2 = PwdUtil.get_password_hash(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = 'test123'
        hashed = PwdUtil.get_password_hash(password)
        assert PwdUtil.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = 'test123'
        hashed = PwdUtil.get_password_hash(password)
        assert PwdUtil.verify_password('wrong', hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        hashed = PwdUtil.get_password_hash('test123')
        assert PwdUtil.verify_password('', hashed) is False

    def test_hash_empty_password_raises_error(self):
        """Test hashing None password raises ValueError."""
        with pytest.raises(ValueError, match='密码不能为空'):
            PwdUtil.get_password_hash(None)

    def test_hash_empty_string_works(self):
        """Test hashing empty string works (not None)."""
        hashed = PwdUtil.get_password_hash('')
        assert isinstance(hashed, str)
        assert PwdUtil.verify_password('', hashed) is True

    def test_hash_long_password(self):
        """Test hashing very long password (bcrypt 72-byte limit)."""
        long_password = 'a' * 1000
        hashed = PwdUtil.get_password_hash(long_password)
        # Should verify with truncated version
        assert PwdUtil.verify_password(long_password, hashed) is True

    def test_hash_special_characters(self):
        """Test hashing password with special characters."""
        password = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        hashed = PwdUtil.get_password_hash(password)
        assert PwdUtil.verify_password(password, hashed) is True

    def test_hash_unicode_characters(self):
        """Test hashing password with unicode characters."""
        password = '密码123🔒'
        hashed = PwdUtil.get_password_hash(password)
        assert PwdUtil.verify_password(password, hashed) is True

    def test_sanitize_password(self):
        """Test password sanitization for bcrypt 72-byte limit."""
        long_password = 'a' * 100
        sanitized = PwdUtil.sanitize_password(long_password)
        assert isinstance(sanitized, str)
        assert len(sanitized.encode('utf-8')) <= 72

    def test_verify_password_with_none(self):
        """Test verify_password returns False for None inputs."""
        hashed = PwdUtil.get_password_hash('test123')
        assert PwdUtil.verify_password(None, hashed) is False
        assert PwdUtil.verify_password('test123', None) is False

    @given(st.text(min_size=1, max_size=50))
    @pytest.mark.slow
    @pytest.mark.hypothesis(deadline=None)
    def test_password_round_trip(self, password: str):
        """Property test: any password should hash and verify correctly."""
        hashed = PwdUtil.get_password_hash(password)
        assert PwdUtil.verify_password(password, hashed) is True

    @given(st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=50))
    @pytest.mark.slow
    @pytest.mark.hypothesis(deadline=None)
    def test_different_passwords_dont_match(self, password1: str, password2: str):
        """Property test: different passwords should not verify."""
        if password1 == password2:
            return  # Skip if passwords are the same

        hashed = PwdUtil.get_password_hash(password1)
        assert PwdUtil.verify_password(password2, hashed) is False
