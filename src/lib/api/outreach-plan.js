import { apiFetch, API_PREFIX } from './client.js';

export function generateOutreachPlan(options) {
  return apiFetch(`${API_PREFIX}/ai/outreach-plan/generate`, { method: 'POST', ...options });
}
