"""Integration tests for student endpoints."""
import pytest


class TestStudentEndpoints:
    """Test cases for student endpoints."""

    def test_list_students(self, client, auth_headers_professor, test_student):
        """Test listing students."""
        response = client.get('/students/', headers=auth_headers_professor)

        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data
        assert 'total' in data
        assert len(data['items']) >= 1

    def test_list_students_unauthorized(self, client):
        """Test listing students without auth."""
        response = client.get('/students/')

        assert response.status_code == 401

    def test_create_student(self, client, auth_headers_professor):
        """Test creating a student."""
        response = client.post('/students/', headers=auth_headers_professor, json={
            'first_name': 'New',
            'last_name': 'Student',
            'course': 'boxing'
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['first_name'] == 'New'
        assert data['last_name'] == 'Student'
        assert data['course'] == 'boxing'

    def test_create_student_invalid_course(self, client, auth_headers_professor):
        """Test creating student with invalid course."""
        response = client.post('/students/', headers=auth_headers_professor, json={
            'first_name': 'New',
            'last_name': 'Student',
            'course': 'invalid_course'
        })

        assert response.status_code == 400

    def test_create_student_missing_fields(self, client, auth_headers_professor):
        """Test creating student with missing fields."""
        response = client.post('/students/', headers=auth_headers_professor, json={
            'first_name': 'New'
            # Missing last_name and course
        })

        assert response.status_code == 400

    def test_get_student(self, client, auth_headers_professor, test_student):
        """Test getting a student."""
        response = client.get(f'/students/{test_student.id}', headers=auth_headers_professor)

        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == str(test_student.id)
        assert data['first_name'] == test_student.first_name

    def test_get_student_not_found(self, client, auth_headers_professor):
        """Test getting nonexistent student."""
        response = client.get('/students/12345678-1234-1234-1234-123456789abc', headers=auth_headers_professor)

        assert response.status_code == 404

    def test_update_student(self, client, auth_headers_professor, test_student):
        """Test updating a student."""
        response = client.put(f'/students/{test_student.id}', headers=auth_headers_professor, json={
            'first_name': 'Updated',
            'phone': '1234567890'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['first_name'] == 'Updated'
        assert data['phone'] == '1234567890'

    def test_delete_student(self, client, auth_headers_professor, test_student):
        """Test deleting a student."""
        response = client.delete(f'/students/{test_student.id}', headers=auth_headers_professor)

        assert response.status_code == 200

        # Verify deleted
        response = client.get(f'/students/{test_student.id}', headers=auth_headers_professor)
        assert response.status_code == 404

    def test_search_students(self, client, auth_headers_professor, test_student):
        """Test searching students."""
        response = client.get('/students/search?q=Test', headers=auth_headers_professor)

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 1

    def test_search_students_short_query(self, client, auth_headers_professor):
        """Test searching with short query."""
        response = client.get('/students/search?q=a', headers=auth_headers_professor)

        assert response.status_code == 400

    def test_deactivate_student(self, client, auth_headers_professor, test_student):
        """Test deactivating a student."""
        response = client.post(f'/students/{test_student.id}/deactivate', headers=auth_headers_professor)

        assert response.status_code == 200
        data = response.get_json()
        assert data['is_active'] == False

    def test_activate_student(self, client, auth_headers_professor, test_student):
        """Test activating a student."""
        # First deactivate
        client.post(f'/students/{test_student.id}/deactivate', headers=auth_headers_professor)

        # Then activate
        response = client.post(f'/students/{test_student.id}/activate', headers=auth_headers_professor)

        assert response.status_code == 200
        data = response.get_json()
        assert data['is_active'] == True

    def test_filter_students_by_course(self, client, auth_headers_professor, test_student):
        """Test filtering students by course."""
        response = client.get('/students/?course=boxing', headers=auth_headers_professor)

        assert response.status_code == 200
        data = response.get_json()
        for student in data['items']:
            assert student['course'] == 'boxing'

    def test_filter_students_by_active(self, client, auth_headers_professor, test_student):
        """Test filtering students by active status."""
        response = client.get('/students/?is_active=true', headers=auth_headers_professor)

        assert response.status_code == 200
        data = response.get_json()
        for student in data['items']:
            assert student['is_active'] == True
