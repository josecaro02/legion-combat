const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

/**
 * Make authenticated GET request
 * @param {string} endpoint
 * @param {string} token - JWT token
 * @returns {Promise<any>}
 */
export async function authGet(endpoint, token) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || data.error || 'Request failed');
  }

  return data;
}

/**
 * Make authenticated POST request
 * @param {string} endpoint
 * @param {object} body
 * @param {string} token - JWT token
 * @returns {Promise<any>}
 */
export async function authPost(endpoint, body, token) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || data.error || 'Request failed');
  }

  return data;
}
