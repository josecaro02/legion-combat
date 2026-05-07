// DEPRECATED: Este archivo está obsoleto y se mantiene solo para compatibilidad
// Todas las llamadas a API ahora deben usar fetchWrapper.js
//
// NO USAR ESTE MÓDULO - SERÁ ELIMINADO EN FUTURO

import { fetchGet, fetchPost, fetchPut, fetchDelete, getAccessToken } from '../utils/fetchWrapper';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

/**
 * @deprecated Use fetchWrapper.js functions directly
 * Make authenticated GET request using new wrapper
 */
export async function authGet(endpoint, token = null) {
  const url = `${API_URL}${endpoint}`;
  // Si se pasa token (old API), se ignora y se usa el del wrapper
  return fetchGet(url);
}

/**
 * @deprecated Use fetchWrapper.js functions directly
 * Make authenticated POST request using new wrapper
 */
export async function authPost(endpoint, body, token = null) {
  const url = `${API_URL}${endpoint}`;
  // Si se pasa token (old API), se ignora y se usa el del wrapper
  return fetchPost(url, body);
}

/**
 * @deprecated Use fetchWrapper.js functions directly
 * Make authenticated PUT request using new wrapper
 */
export async function authPut(endpoint, body, token = null) {
  const url = `${API_URL}${endpoint}`;
  // Si se pasa token (old API), se ignora y se usa el del wrapper
  return fetchPut(url, body);
}

/**
 * @deprecated Use fetchWrapper.js functions directly
 * Make authenticated DELETE request using new wrapper
 */
export async function authDelete(endpoint, token = null) {
  const url = `${API_URL}${endpoint}`;
  // Si se pasa token (old API), se ignora y se usa el del wrapper
  return fetchDelete(url);
}
