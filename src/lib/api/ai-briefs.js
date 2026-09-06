import { apiFetch, API_PREFIX } from './client.js';

export function listAiBriefs({ student_id, latest } = {}, options) {
  return apiFetch(`${API_PREFIX}/ai-briefs`, { query: { student_id, latest }, ...options });
}

export function getAiBrief(id, options) {
  return apiFetch(`${API_PREFIX}/ai-briefs/${id}`, options);
}

export function createAiBrief(payload, options) {
  return apiFetch(`${API_PREFIX}/ai-briefs`, { method: 'POST', body: payload, ...options });
}

export function updateAiBrief(id, updates, options) {
  return apiFetch(`${API_PREFIX}/ai-briefs/${id}`, { method: 'PATCH', body: updates, ...options });
}

export function deleteAiBrief(id, options) {
  return apiFetch(`${API_PREFIX}/ai-briefs/${id}`, { method: 'DELETE', ...options });
}

export function approveAiBrief(id, options) {
  return apiFetch(`${API_PREFIX}/ai-briefs/${id}/approve`, { method: 'POST', ...options });
}

export function supersedeAiBrief(id, options) {
  return apiFetch(`${API_PREFIX}/ai-briefs/${id}/supersede`, { method: 'POST', ...options });
}
