import { apiFetch, API_PREFIX } from './client.js';

export function loadContactLoopData(options) {
  return apiFetch(`${API_PREFIX}/data/load`, options);
}

export function getDashboardSummary({ from, to } = {}, options) {
  return apiFetch(`${API_PREFIX}/dashboard/summary`, { query: { from, to }, ...options });
}
