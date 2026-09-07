import { apiFetch, API_PREFIX } from './client.js';
import { clearStoredToken, setStoredToken } from './auth-token.js';

export async function register({ email, password, name }) {
  const result = await apiFetch(`${API_PREFIX}/auth/register`, {
    method: 'POST',
    body: { email, password, name: name || null },
  });
  setStoredToken(result?.token);
  return result?.user ?? null;
}

export async function login({ email, password }) {
  const result = await apiFetch(`${API_PREFIX}/auth/login`, {
    method: 'POST',
    body: { email, password },
  });
  setStoredToken(result?.token);
  return result?.user ?? null;
}

export async function fetchMe() {
  try {
    return await apiFetch(`${API_PREFIX}/auth/me`);
  } catch {
    return null;
  }
}

export async function logout() {
  try {
    await apiFetch(`${API_PREFIX}/auth/logout`, { method: 'POST' });
  } finally {
    clearStoredToken();
  }
}
