import { apiFetch, API_PREFIX } from './client.js';

export function generateContactBrief(body, options) {
  return apiFetch(`${API_PREFIX}/ai/contact-brief/generate`, { method: 'POST', body, ...options });
}
