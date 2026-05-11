import { authGet, authPost, authPut } from './client';

const ENDPOINT = '/students';

/**
 * Get list of students
 * @param {string} token - JWT token
 * @param {Object} params - Query parameters
 * @returns {Promise<{items: Array, total: number, pages: number, current_page: number}>}
 */
export async function getStudents(token, params = {}) {
  const queryParams = new URLSearchParams();

  if (params.page) queryParams.append('page', params.page);
  if (params.per_page) queryParams.append('per_page', params.per_page);
  if (params.course) queryParams.append('course', params.course);
  if (params.is_active !== undefined) queryParams.append('is_active', params.is_active);

  const queryString = queryParams.toString();
  const url = queryString ? `${ENDPOINT}/?${queryString}` : `${ENDPOINT}/`;

  return authGet(url, token);
}

/**
 * Create a new student
 * @param {string} token - JWT token
 * @param {Object} data - Student data
 * @param {string} data.first_name
 * @param {string} data.last_name
 * @param {string} data.course - 'boxing', 'kickboxing', or 'boxing_school'
 * @param {string} data.emergency_contact_name
 * @param {string} data.emergency_contact_phone
 * @param {string} [data.address]
 * @param {string} [data.phone]
 * @param {string} [data.photo_url]
 * @param {string} [data.enrollment_date]
 * @returns {Promise<Object>}
 */
export async function createStudent(token, data) {
  return authPost(ENDPOINT + '/', data, token);
}

/**
 * Update an existing student
 * @param {string} token - JWT token
 * @param {string} studentId - Student UUID
 * @param {Object} data - Student data to update
 * @param {string} [data.first_name]
 * @param {string} [data.last_name]
 * @param {string} [data.course]
 * @param {string} [data.emergency_contact_name]
 * @param {string} [data.emergency_contact_phone]
 * @param {string} [data.photo_url]
 * @param {string} [data.address]
 * @param {string} [data.phone]
 * @param {boolean} [data.is_active]
 * @returns {Promise<Object>}
 */
export async function updateStudent(token, studentId, data) {
  const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}${ENDPOINT}/${studentId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  const result = await response.json();

  if (!response.ok) {
    throw new Error(result.message || result.error || 'Request failed');
  }

  return result;
}

/**
 * Search students by name
 * @param {string} token - JWT token
 * @param {string} query - Search query (min 2 characters)
 * @returns {Promise<Array>}
 */
export async function searchStudents(token, query) {
  return authGet(`${ENDPOINT}/search?q=${encodeURIComponent(query)}`, token);
}

/**
 * Get a single student by ID
 * @param {string} token - JWT token
 * @param {string} studentId
 * @returns {Promise<Object>}
 */
export async function getStudent(token, studentId) {
  return authGet(`${ENDPOINT}/${studentId}`, token);
}


/**
 * Deactivate a student
 * @param {string} token - JWT token
 * @param {string} studentId
 * @returns {Promise<Object>}
 */
export async function deactivateStudent(token, studentId) {
  return authPost(`${ENDPOINT}/${studentId}/deactivate`, {}, token);
}

/**
 * Activate a student
 * @param {string} token - JWT token
 * @param {string} studentId
 * @returns {Promise<Object>}
 */
export async function activateStudent(token, studentId) {
  return authPost(`${ENDPOINT}/${studentId}/activate`, {}, token);
}


/**
 * Get students with upcoming payments due within N days
 * @param {string} token - JWT token
 * @param {number} days - Number of days to look ahead (default: 5)
 * @returns {Promise<Array>}
 */
export async function getUpcomingPayments(token, days = 5) {
  return authGet(`${ENDPOINT}/upcoming-payments?days=${days}`, token);
}
