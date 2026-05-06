const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

/**
 * Login user with email and password
 * Persists both access_token and refresh_token to localStorage
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

  // Persistir ambos tokens en localStorage
  if (data.access_token) {
    localStorage.setItem('access_token', data.access_token);
  }
  if (data.refresh_token) {
    localStorage.setItem('refresh_token', data.refresh_token);
  }

  return {
    token: data.access_token,
    user: {
      id: data.user.user_id,
      email: data.user.email,
      role: data.user.role,
    },
  };
}

/**
 * Refresh access token using refresh token
 * @returns {Promise<{access_token: string, refresh_token?: string}>}
 * @throws {Error} On failed refresh
 */
export async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');

  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || data.error || 'Token refresh failed');
  }

  // Actualizar tokens en localStorage
  if (data.access_token) {
    localStorage.setItem('access_token', data.access_token);
  }
  if (data.refresh_token) {
    localStorage.setItem('refresh_token', data.refresh_token);
  }

  return {
    access_token: data.access_token,
    refresh_token: data.refresh_token || refreshToken,
  };
}

/**
 * Clear all auth tokens from localStorage
 */
export function clearAuth() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}
