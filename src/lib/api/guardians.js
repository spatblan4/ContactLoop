import { apiFetch, API_PREFIX } from './client.js';

export function listGuardians({ student_id } = {}, options) {
  return apiFetch(`${API_PREFIX}/guardians`, { query: { student_id }, ...options });
}

export function getGuardian(id, options) {
  return apiFetch(`${API_PREFIX}/guardians/${id}`, options);
}

export function createGuardian(payload, options) {
  return apiFetch(`${API_PREFIX}/guardians`, { method: 'POST', body: payload, ...options });
}

export function updateGuardian(id, updates, options) {
  return apiFetch(`${API_PREFIX}/guardians/${id}`, { method: 'PATCH', body: updates, ...options });
}

export function deleteGuardian(id, options) {
  return apiFetch(`${API_PREFIX}/guardians/${id}`, { method: 'DELETE', ...options });
}
