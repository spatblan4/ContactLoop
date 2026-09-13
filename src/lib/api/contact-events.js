import { apiFetch, API_PREFIX } from './client.js';

export function listContactEvents({ student_id, from, to, result } = {}, options) {
  return apiFetch(`${API_PREFIX}/contact-events`, { query: { student_id, from, to, result }, ...options });
}

export function getContactEvent(id, options) {
  return apiFetch(`${API_PREFIX}/contact-events/${id}`, options);
}

export function createContactEvent(payload, options) {
  return apiFetch(`${API_PREFIX}/contact-events`, { method: 'POST', body: payload, ...options });
}

export function updateContactEvent(id, updates, options) {
  return apiFetch(`${API_PREFIX}/contact-events/${id}`, { method: 'PATCH', body: updates, ...options });
}

export function deleteContactEvent(id, options) {
  return apiFetch(`${API_PREFIX}/contact-events/${id}`, { method: 'DELETE', ...options });
}

export function generateCallSummary(contactEventId, options) {
  return apiFetch(`${API_PREFIX}/ai/call-summary/generate`, {
    method: 'POST',
    body: { contact_event_id: contactEventId },
    ...options,
  });
}
