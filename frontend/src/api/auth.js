const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

/**
 * Login user with email and password
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{token: string, user: {id, email, role}}}
 * @throws {Error} On failed login
 */
export async function login(email, password) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || data.error || 'Login failed');
  }

  return {
    token: data.access_token,
    user: {
      id: data.user_id,
      email: data.email,
      role: data.role,
    },
  };
}
