// API configuration and fetch wrappers
// TODO: Implement fetch wrappers with error handling

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export async function fetchGet(endpoint) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return response.json();
}

export async function fetchPost(endpoint, data) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return response.json();
}
