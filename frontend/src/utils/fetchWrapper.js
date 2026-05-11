import { AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY, USER_KEY } from '../auth/constants';
import { clearAuth as clearAuthApi } from '../api/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Estado del proceso de refresco
let isRefreshing = false;
let refreshPromise = null;

// Cola de peticiones pendientes de reintentar
let pendingRequests = [];

/**
 * Agrega una petición a la cola para reintentar tras refresh
 * @param {Function} resolve - Función para resolver la promesa
 * @param {Function} reject - Función para rechazar la promesa
 */
function addPendingRequest(resolve, reject) {
  pendingRequests.push({ resolve, reject });
}

/**
 * Reintentar todas las peticiones en cola
 * @param {string} newAccessToken - Nuevo token de acceso
 */
function retryPendingRequests(newAccessToken) {
  pendingRequests.forEach(({ resolve, reject }) => {
    try {
      resolve(newAccessToken);
    } catch (error) {
      reject(error);
    }
  });
  pendingRequests = [];
}

/**
 * Obtener el token de acceso de localStorage
 * @returns {string|null}
 */
export function getAccessToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Obtener el token de refresh de localStorage
 * @returns {string|null}
 */
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Llamada al endpoint de refresh para obtener un nuevo token
 * @returns {Promise<{access_token: string, refresh_token: string}>}
 */
async function refreshAccessToken() {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    clearAuthApi(true);
    throw new Error('No refresh token available');
  }

  try {
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

    // Guardar el nuevo token de acceso y opcionalmente el refresh
    if (data.access_token) {
      localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
    }
    if (data.refresh_token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
    }

    return {
      access_token: data.access_token,
      refresh_token: data.refresh_token || refreshToken,
    };
  } catch (error) {
    clearAuthApi(true);
    throw error;
  }
}

/**
 * Procesar respuesta de error 401 con retry automático
 * @param {string} originalUrl - URL de la petición original
 * @param {RequestInit} originalOptions - Opciones de la petición original
 * @param {number} retryCount - Número de reintentos
 * @returns {Promise<Response>}
 */
async function handle401Error(originalUrl, originalOptions, retryCount = 0) {
  if (isRefreshing || !getRefreshToken()) {
    clearAuthApi(true);
    throw new Error('Session expired. Please login again.');
  }

  // Si ya estamos intentando refresh, agregar a la cola
  if (retryCount === 0 && isRefreshing) {
    return new Promise((resolve, reject) => {
      addPendingRequest(resolve, reject);
    });
  }

  // Evitar múltiples llamadas concurrentes a refresh
  if (!isRefreshing) {
    isRefreshing = true;
    refreshPromise = refreshAccessToken();
  }

  try {
    const { access_token: newAccessToken } = await refreshPromise;

    // Reintentar la petición original con el nuevo token
    const newOptions = {
      ...originalOptions,
      headers: {
        ...originalOptions.headers,
        'Authorization': `Bearer ${newAccessToken}`,
      },
    };

    // Reintentar la petición
    const response = await fetch(originalUrl, newOptions);

    if (!response.ok) {
      // Si la petición reintentada falla con 401, limpiar auth
      if (response.status === 401) {
        clearAuthApi(true);
        throw new Error('Session expired. Please login again.');
      }
      return response;
    }

    // Limpiar cola y resetear estado
    isRefreshing = false;
    refreshPromise = null;
    retryPendingRequests(newAccessToken);

    return response;
  } catch (error) {
    isRefreshing = false;
    refreshPromise = null;
    // Rechazar todas las peticiones en cola
    pendingRequests.forEach(({ reject }) => reject(error));
    pendingRequests = [];
    throw error;
  }
}

/**
 * Wrapper personalizado de fetch con manejo automático de tokens
 * @param {string} url - URL a llamar
 * @param {RequestInit} options - Opciones del fetch
 * @returns {Promise<Response>}
 */
export async function fetchWithAuth(url, options = {}) {
  const accessToken = getAccessToken();

  const finalOptions = {
    ...options,
    headers: {
      ...options.headers,
      'Content-Type': 'application/json',
      ...(accessToken && { 'Authorization': `Bearer ${accessToken}` }),
    },
  };

  const fullUrl = `${API_URL}${url}`;

  const response = await fetch(fullUrl, finalOptions);

  if (response.status === 401) {
    return handle401Error(fullUrl, finalOptions);
  }

  return response;
}

/**
 * Convenience function para GET requests
 * @param {string} url - URL completa (incluye API_URL)
 * @param {RequestInit} options - Opciones adicionales
 * @returns {Promise<any>}
 */
export async function fetchGet(url, options = {}) {
  const response = await fetchWithAuth(url, { ...options, method: 'GET' });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.message || data.error || 'Request failed');
  }

  return response.json();
}

/**
 * Convenience function para POST requests
 * @param {string} url - URL completa (incluye API_URL)
 * @param {object} data - Datos a enviar
 * @param {RequestInit} options - Opciones adicionales
 * @returns {Promise<any>}
 */
export async function fetchPost(url, data = {}, options = {}) {
  const response = await fetchWithAuth(url, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || errorData.error || 'Request failed');
  }

  return response.json();
}

/**
 * Convenience function para PUT requests
 * @param {string} url - URL completa (incluye API_URL)
 * @param {object} data - Datos a enviar
 * @param {RequestInit} options - Opciones adicionales
 * @returns {Promise<any>}
 */
export async function fetchPut(url, data = {}, options = {}) {
  const response = await fetchWithAuth(url, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || errorData.error || 'Request failed');
  }

  return response.json();
}

/**
 * Convenience function para DELETE requests
 * @param {string} url - URL completa (incluye API_URL)
 * @param {RequestInit} options - Opciones adicionales
 * @returns {Promise<any>}
 */
export async function fetchDelete(url, options = {}) {
  const response = await fetchWithAuth(url, {
    ...options,
    method: 'DELETE',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || errorData.error || 'Request failed');
  }

  return response.json();
}
