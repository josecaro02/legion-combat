"""Integration tests for authentication endpoints."""
import pytest


class TestAuthEndpoints:
    """Test cases for authentication endpoints."""

    def test_login_success(self, client, test_owner):
        """Test successful login."""
        response = client.post('/auth/login', json={
            'email': 'owner@test.com',
            'password': 'password123'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'bearer'

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', json={
            'email': 'wrong@test.com',
            'password': 'wrongpassword'
        })

        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post('/auth/login', json={
            'email': 'test@test.com'
            # Missing password
        })

        assert response.status_code == 400

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get('/students/')

        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get('/students/', headers={
            'Authorization': 'Bearer invalid-token'
        })

        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers_owner):
        """Test getting current user info."""
        response = client.get('/auth/me', headers=auth_headers_owner)

        assert response.status_code == 200
        data = response.get_json()
        assert data['email'] == 'owner@test.com'
        assert data['role'] == 'owner'

    def test_change_password(self, client, auth_headers_owner, test_owner):
        """Test changing password."""
        response = client.put('/auth/me/password', headers=auth_headers_owner, json={
            'old_password': 'password123',
            'new_password': 'newpassword123'
        })

        assert response.status_code == 200

        # Verify new password works
        response = client.post('/auth/login', json={
            'email': 'owner@test.com',
            'password': 'newpassword123'
        })
        assert response.status_code == 200

    def test_change_password_wrong_old(self, client, auth_headers_owner):
        """Test changing password with wrong old password."""
        response = client.put('/auth/me/password', headers=auth_headers_owner, json={
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123'
        })

        assert response.status_code == 400

    def test_logout(self, client, auth_headers_owner):
        """Test logout."""
        response = client.post('/auth/logout', headers=auth_headers_owner)

        assert response.status_code == 200

    def test_logout_all(self, client, auth_headers_owner):
        """Test logout from all sessions."""
        response = client.post('/auth/logout-all', headers=auth_headers_owner)

        assert response.status_code == 200
        data = response.get_json()
        assert 'revoked_count' in data

    def test_refresh_token(self, client, test_owner):
        """Test refreshing token."""
        # First login
        response = client.post('/auth/login', json={
            'email': 'owner@test.com',
            'password': 'password123'
        })
        tokens = response.get_json()

        # Refresh
        response = client.post('/auth/refresh', json={
            'refresh_token': tokens['refresh_token']
        })

        assert response.status_code == 200
        new_tokens = response.get_json()
        assert 'access_token' in new_tokens
        assert 'refresh_token' in new_tokens
        # Should get new refresh token
        assert new_tokens['refresh_token'] != tokens['refresh_token']

    def test_refresh_token_reuse(self, client, test_owner):
        """Test refresh token reuse detection."""
        # First login
        response = client.post('/auth/login', json={
            'email': 'owner@test.com',
            'password': 'password123'
        })
        tokens = response.get_json()

        # First refresh
        response = client.post('/auth/refresh', json={
            'refresh_token': tokens['refresh_token']
        })
        assert response.status_code == 200

        # Second refresh with same token should fail
        response = client.post('/auth/refresh', json={
            'refresh_token': tokens['refresh_token']
        })
        assert response.status_code == 401
        assert 'reuse' in response.get_json()['message'].lower()
