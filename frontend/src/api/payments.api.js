import { fetchGet, fetchPost } from '../utils/fetchWrapper';

const ENDPOINT = '/payments';

/**
 * Quick Pay - Create payment and mark as paid in one operation
 * @param {Object} data - Payment data
 * @param {string} data.student_id - Student UUID
 * @param {number} data.amount - Payment amount
 * @param {string} [data.notes] - Optional notes
 * @returns {Promise<Object>} Created payment with status "paid"
 */
export async function quickPay(data) {
  return fetchPost(`${ENDPOINT}/quick-pay`, data);
}

/**
 * Get list of payments
 * @param {Object} params - Query parameters
 * @returns {Promise<{items: Array, total: number, pages: number, current_page: number}>}
 */
export async function getPayments(params = {}) {
  const queryParams = new URLSearchParams();

  if (params.page) queryParams.append('page', params.page);
  if (params.per_page) queryParams.append('per_page', params.per_page);
  if (params.status) queryParams.append('status', params.status);

  const queryString = queryParams.toString();
  const url = queryString ? `${ENDPOINT}/?${queryString}` : `${ENDPOINT}/`;

  return fetchGet(url);
}

/**
 * Get payments for a specific student
 * @param {string} studentId - Student UUID
 * @param {Object} params - Query parameters
 * @returns {Promise<{items: Array, total: number, pages: number, current_page: number}>}
 */
export async function getStudentPayments(studentId, params = {}) {
  const queryParams = new URLSearchParams();

  if (params.page) queryParams.append('page', params.page);
  if (params.per_page) queryParams.append('per_page', params.per_page);
  if (params.status) queryParams.append('status', params.status);

  const queryString = queryParams.toString();
  const url = queryString
    ? `${ENDPOINT}/student/${studentId}?${queryString}`
    : `${ENDPOINT}/student/${studentId}`;

  return fetchGet(url);
}

/**
 * Get a single payment by ID
 * @param {string} paymentId - Payment UUID
 * @returns {Promise<Object>}
 */
export async function getPayment(paymentId) {
  return fetchGet(`${ENDPOINT}/${paymentId}`);
}
