import { fetchGet, fetchPost, fetchPut } from '../utils/fetchWrapper';

const ENDPOINT = '/students';

/**
 * Get list of students
 * @param {Object} params - Query parameters
 * @returns {Promise<{items: Array, total: number, pages: number, current_page: number}>}
 */
export async function getStudents(params = {}) {
  const queryParams = new URLSearchParams();

  if (params.page) queryParams.append('page', params.page);
  if (params.per_page) queryParams.append('per_page', params.per_page);
  if (params.course) queryParams.append('course', params.course);
  if (params.is_active !== undefined) queryParams.append('is_active', params.is_active);

  const queryString = queryParams.toString();
  const url = queryString ? `${ENDPOINT}/?${queryString}` : `${ENDPOINT}/`;

  return fetchGet(url);
}

/**
 * Create a new student
 * @param {Object} data - Student data
 * @param {string} data.first_name
 * @param {string} data.last_name
 * @param {string} data.course - 'boxing', 'kickboxing', or 'both'
 * @param {string} data.emergency_contact_name
 * @param {string} data.emergency_contact_phone
 * @param {string} [data.address]
 * @param {string} [data.phone]
 * @param {string} [data.photo_url]
 * @param {string} [data.enrollment_date]
 * @returns {Promise<Object>}
 */
export async function createStudent(data) {
  return fetchPost(ENDPOINT + '/', data);
}

/**
 * Update an existing student
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
export async function updateStudent(studentId, data) {
  return fetchPut(`${ENDPOINT}/${studentId}`, data);
}

/**
 * Search students by name
 * @param {string} query - Search query (min 2 characters)
 * @returns {Promise<Array>}
 */
export async function searchStudents(query) {
  return fetchGet(`${ENDPOINT}/search?q=${encodeURIComponent(query)}`);
}

/**
 * Get a single student by ID
 * @param {string} studentId
 * @returns {Promise<Object>}
 */
export async function getStudent(studentId) {
  return fetchGet(`${ENDPOINT}/${studentId}`);
}


/**
 * Deactivate a student
 * @param {string} studentId
 * @returns {Promise<Object>}
 */
export async function deactivateStudent(studentId) {
  return fetchPost(`${ENDPOINT}/${studentId}/deactivate`, {});
}

/**
 * Activate a student
 * @param {string} studentId
 * @returns {Promise<Object>}
 */
export async function activateStudent(studentId) {
  return fetchPost(`${ENDPOINT}/${studentId}/activate`, {});
}


/**
 * Get students with upcoming payments due within N days
 * @param {number} days - Number of days to look ahead (default: 5)
 * @returns {Promise<Array>}
 */
export async function getUpcomingPayments(days = 5) {
  return fetchGet(`${ENDPOINT}/upcoming-payments?days=${days}`);
}
