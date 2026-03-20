"""Tests for auth service."""
import pytest
from datetime import datetime, timedelta

from app.exceptions.custom_exceptions import AuthenticationError
from app.models.user import User, UserRole
from app.services.auth_service import AuthService
from app.utils.password_utils import hash_password


class TestAuthService:
    """Test cases for AuthService."""

    def test_login_success(self, app, test_owner):
        """Test successful login."""
        with app.app_context():
            service = AuthService()
            tokens = service.login(
                email='owner@test.com',
                password='password123',
                ip_address='127.0.0.1',
                user_agent='Test'
            )

            assert 'access_token' in tokens
            assert 'refresh_token' in tokens
            assert tokens['token_type'] == 'bearer'
            assert tokens['expires_in'] == 900

    def test_login_invalid_email(self, app):
        """Test login with invalid email."""
        with app.app_context():
            service = AuthService()
            with pytest.raises(AuthenticationError):
                service.login(
                    email='nonexistent@test.com',
                    password='password123',
                    ip_address='127.0.0.1',
                    user_agent='Test'
                )

    def test_login_invalid_password(self, app, test_owner):
        """Test login with invalid password."""
        with app.app_context():
            service = AuthService()
            with pytest.raises(AuthenticationError):
                service.login(
                    email='owner@test.com',
                    password='wrongpassword',
                    ip_address='127.0.0.1',
                    user_agent='Test'
                )

    def test_login_inactive_user(self, app):
        """Test login with inactive user."""
        with app.app_context():
            from app.extensions import db
            user = User(
                email='inactive@test.com',
                password_hash=hash_password('password123'),
                first_name='Inactive',
                last_name='User',
                role=UserRole.PROFESSOR,
                is_active=False
            )
            db.session.add(user)
            db.session.commit()

            service = AuthService()
            with pytest.raises(AuthenticationError):
                service.login(
                    email='inactive@test.com',
                    password='password123',
                    ip_address='127.0.0.1',
                    user_agent='Test'
                )

    def test_refresh_token_rotation(self, app, test_owner):
        """Test that refresh token rotates."""
        with app.app_context():
            service = AuthService()

            # Login to get tokens
            tokens = service.login(
                email='owner@test.com',
                password='password123',
                ip_address='127.0.0.1',
                user_agent='Test'
            )

            old_refresh_token = tokens['refresh_token']

            # Refresh
            new_tokens = service.refresh(
                refresh_token_str=old_refresh_token,
                ip_address='127.0.0.1',
                user_agent='Test'
            )

            # Should get new tokens
            assert new_tokens['refresh_token'] != old_refresh_token
            assert 'access_token' in new_tokens

    def test_refresh_token_reuse_detection(self, app, test_owner):
        """Test that reused refresh tokens are detected."""
        with app.app_context():
            service = AuthService()

            # Login to get tokens
            tokens = service.login(
                email='owner@test.com',
                password='password123',
                ip_address='127.0.0.1',
                user_agent='Test'
            )

            refresh_token = tokens['refresh_token']

            # First refresh
            service.refresh(
                refresh_token_str=refresh_token,
                ip_address='127.0.0.1',
                user_agent='Test'
            )

            # Second refresh with same token should fail
            with pytest.raises(AuthenticationError) as exc_info:
                service.refresh(
                    refresh_token_str=refresh_token,
                    ip_address='127.0.0.1',
                    user_agent='Test'
                )

            assert 'reuse' in str(exc_info.value).lower()

    def test_logout(self, app, test_owner):
        """Test logout."""
        with app.app_context():
            service = AuthService()

            # Login
            tokens = service.login(
                email='owner@test.com',
                password='password123',
                ip_address='127.0.0.1',
                user_agent='Test'
            )

            # Get JTI from token
            from app.utils.jwt_utils import decode_token
            payload = decode_token(tokens['refresh_token'])
            jti = payload['jti']

            # Logout
            service.logout(str(test_owner.id), jti)

            # Trying to refresh should fail
            with pytest.raises(AuthenticationError):
                service.refresh(
                    refresh_token_str=tokens['refresh_token'],
                    ip_address='127.0.0.1',
                    user_agent='Test'
                )

    def test_logout_all(self, app, test_owner):
        """Test logout from all sessions."""
        with app.app_context():
            service = AuthService()

            # Login multiple times
            tokens1 = service.login(
                email='owner@test.com',
                password='password123',
                ip_address='127.0.0.1',
                user_agent='Test1'
            )
            tokens2 = service.login(
                email='owner@test.com',
                password='password123',
                ip_address='127.0.0.1',
                user_agent='Test2'
            )

            # Logout all
            count = service.logout_all(str(test_owner.id))
            assert count >= 2

            # Both tokens should be invalid
            with pytest.raises(AuthenticationError):
                service.refresh(
                    refresh_token_str=tokens1['refresh_token'],
                    ip_address='127.0.0.1',
                    user_agent='Test'
                )

            with pytest.raises(AuthenticationError):
                service.refresh(
                    refresh_token_str=tokens2['refresh_token'],
                    ip_address='127.0.0.1',
                    user_agent='Test'
                )
