import { apiFetch, API_PREFIX } from './client.js';

export function listTeacherNotes({ student_id } = {}, options) {
  return apiFetch(`${API_PREFIX}/teacher-notes`, { query: { student_id }, ...options });
}

export function getTeacherNote(id, options) {
  return apiFetch(`${API_PREFIX}/teacher-notes/${id}`, options);
}

export function createTeacherNote(payload, options) {
  return apiFetch(`${API_PREFIX}/teacher-notes`, { method: 'POST', body: payload, ...options });
}

export function updateTeacherNote(id, updates, options) {
  return apiFetch(`${API_PREFIX}/teacher-notes/${id}`, { method: 'PATCH', body: updates, ...options });
}

export function deleteTeacherNote(id, options) {
  return apiFetch(`${API_PREFIX}/teacher-notes/${id}`, { method: 'DELETE', ...options });
}
