// DEPRECATED: Este archivo está obsoleto y se mantiene solo para compatibilidad
// Todas las operaciones de autenticación ahora deben ir en:
// - api/auth.js para las llamadas a API
// - contexts/AuthContext.jsx para el estado de React
// - auth/constants.js para las constantes de localStorage
//
// NO USAR ESTE MÓDULO - SERÁ ELIMINADO EN FUTURO

import { AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY, USER_KEY } from './constants';

/**
 * @deprecated Use api/auth.js instead
 * Get access token from localStorage
 */
export function getToken() {
  console.warn('[DEPRECATED] getToken() is deprecated. Use api/auth.js or useAuth()');
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * @deprecated Use api/auth.js instead
 * Set access token to localStorage (called by login api)
 */
export function setToken(token) {
  console.warn('[DEPRECATED] setToken() is deprecated. Use api/auth.js');
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

/**
 * @deprecated Use api/auth.js instead
 * Remove access token from localStorage
 */
export function removeToken() {
  console.warn('[DEPRECATED] removeToken() is deprecated. Use api/auth.js');
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

/**
 * @deprecated Use api/auth.js instead
 * Check if user is authenticated
 */
export function isAuthenticated() {
  console.warn('[DEPRECATED] isAuthenticated() is deprecated. Use useAuth() hook');
  return !!localStorage.getItem(AUTH_TOKEN_KEY);
}

// Exportaciones para compatibilidad
export { AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY, USER_KEY };
