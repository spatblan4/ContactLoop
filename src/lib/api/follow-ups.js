import { apiFetch, API_PREFIX } from './client.js';

export function listFollowUps({ status, student_id } = {}, options) {
  return apiFetch(`${API_PREFIX}/follow-ups`, { query: { status, student_id }, ...options });
}

export function getFollowUp(id, options) {
  return apiFetch(`${API_PREFIX}/follow-ups/${id}`, options);
}

export function createFollowUp(payload, options) {
  return apiFetch(`${API_PREFIX}/follow-ups`, { method: 'POST', body: payload, ...options });
}

export function updateFollowUp(id, updates, options) {
  return apiFetch(`${API_PREFIX}/follow-ups/${id}`, { method: 'PATCH', body: updates, ...options });
}

export function deleteFollowUp(id, options) {
  return apiFetch(`${API_PREFIX}/follow-ups/${id}`, { method: 'DELETE', ...options });
}
