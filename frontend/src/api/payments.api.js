import { authGet, authPost } from './client';

const ENDPOINT = '/payments';

/**
 * Quick Pay - Create payment and mark as paid in one operation
 * @param {string} token - JWT token
 * @param {Object} data - Payment data
 * @param {string} data.student_id - Student UUID
 * @param {number} data.amount - Payment amount
 * @param {string} [data.notes] - Optional notes
 * @returns {Promise<Object>} Created payment with status "paid"
 */
export async function quickPay(token, data) {
  return authPost(`${ENDPOINT}/quick-pay`, data, token);
}

/**
 * Get list of payments
 * @param {string} token - JWT token
 * @param {Object} params - Query parameters
 * @returns {Promise<{items: Array, total: number, pages: number, current_page: number}>}
 */
export async function getPayments(token, params = {}) {
  const queryParams = new URLSearchParams();

  if (params.page) queryParams.append('page', params.page);
  if (params.per_page) queryParams.append('per_page', params.per_page);
  if (params.status) queryParams.append('status', params.status);

  const queryString = queryParams.toString();
  const url = queryString ? `${ENDPOINT}/?${queryString}` : `${ENDPOINT}/`;

  return authGet(url, token);
}

/**
 * Get payments for a specific student
 * @param {string} token - JWT token
 * @param {string} studentId - Student UUID
 * @param {Object} params - Query parameters
 * @returns {Promise<{items: Array, total: number, pages: number, current_page: number}>}
 */
export async function getStudentPayments(token, studentId, params = {}) {
  const queryParams = new URLSearchParams();

  if (params.page) queryParams.append('page', params.page);
  if (params.per_page) queryParams.append('per_page', params.per_page);
  if (params.status) queryParams.append('status', params.status);

  const queryString = queryParams.toString();
  const url = queryString
    ? `${ENDPOINT}/student/${studentId}?${queryString}`
    : `${ENDPOINT}/student/${studentId}`;

  return authGet(url, token);
}

/**
 * Get a single payment by ID
 * @param {string} token - JWT token
 * @param {string} paymentId - Payment UUID
 * @returns {Promise<Object>}
 */
export async function getPayment(token, paymentId) {
  return authGet(`${ENDPOINT}/${paymentId}`, token);
}
