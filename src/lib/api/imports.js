import { apiFetch, API_PREFIX } from './client.js';

export function importStudents(payload, options) {
  return apiFetch(`${API_PREFIX}/import/students`, { method: 'POST', body: payload, ...options });
}
