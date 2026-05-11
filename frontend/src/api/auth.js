import { AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY, USER_KEY, EXPIRY_KEY } from '../auth/constants';

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
    localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
  }
  if (data.refresh_token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  }

  // Calcular y guardar expiry (24 horas desde now)
  const expiry = Date.now() + 24 * 60 * 60 * 1000;
  localStorage.setItem(EXPIRY_KEY, expiry);

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
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

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
    localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
  }
  if (data.refresh_token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  }

  // Actualizar expiry
  const expiry = Date.now() + 24 * 60 * 60 * 1000;
  localStorage.setItem(EXPIRY_KEY, expiry);

  return {
    access_token: data.access_token,
    refresh_token: data.refresh_token || refreshToken,
  };
}

/**
 * Clear all auth tokens from localStorage and redirect to login
 * @param {boolean} redirect - Whether to redirect to login (default: true)
 */
export function clearAuth(redirect = true) {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(EXPIRY_KEY);

  if (redirect) {
    window.location.href = '/login';
  }
}

/**
 * Check if the current session is expired
 * @returns {boolean}
 */
export function isTokenExpired() {
  const storedExpiry = localStorage.getItem(EXPIRY_KEY);
  if (!storedExpiry) return true;

  const expiry = parseInt(storedExpiry, 10);
  return Date.now() > expiry;
}

/**
 * Get the current access token from localStorage
 * @returns {string|null}
 */
export function getAccessToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Get the current refresh token from localStorage
 * @returns {string|null}
 */
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Get stored user data from localStorage
 * @returns {object|null}
 */
export function getUser() {
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;

  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}
