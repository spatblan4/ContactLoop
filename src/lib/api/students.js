import { apiFetch, API_PREFIX } from './client.js';

export function listStudents({ search } = {}, options) {
  return apiFetch(`${API_PREFIX}/students`, { query: { search }, ...options });
}

export function getStudent(id, options) {
  return apiFetch(`${API_PREFIX}/students/${id}`, options);
}

export function createStudent(payload, options) {
  return apiFetch(`${API_PREFIX}/students`, { method: 'POST', body: payload, ...options });
}

export function updateStudent(id, updates, options) {
  return apiFetch(`${API_PREFIX}/students/${id}`, { method: 'PATCH', body: updates, ...options });
}

export function deleteStudent(id, options) {
  return apiFetch(`${API_PREFIX}/students/${id}`, { method: 'DELETE', ...options });
}
