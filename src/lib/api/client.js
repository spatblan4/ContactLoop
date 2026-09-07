let apiBaseUrlOverride = null;

function normalizeBaseUrl(value) {
  return String(value ?? '').trim().replace(/\/+$/, '');
}

const SAME_ORIGIN = 'same-origin';

function isSameOrigin(value) {
  return String(value ?? '').trim().toLowerCase() === SAME_ORIGIN;
}

function configuredBaseUrl() {
  return apiBaseUrlOverride ?? import.meta.env?.VITE_API_BASE_URL;
}

export function setApiBaseUrl(url) {
  apiBaseUrlOverride = url === null || url === undefined ? null : normalizeBaseUrl(url);
}

export function getApiBaseUrl() {
  const configured = configuredBaseUrl();
  if (isSameOrigin(configured)) return '';
  return normalizeBaseUrl(configured);
}

export function hasBackendConfig() {
  const configured = configuredBaseUrl();
  if (isSameOrigin(configured)) return true;
  return Boolean(normalizeBaseUrl(configured));
}

export const API_PREFIX = '/api/v1';

export class ApiError extends Error {
  constructor(message, { status = null, detail = undefined, url = '', method = '' } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.url = url;
    this.method = method;
  }
}

function extractDetail(payload) {
  if (payload === null || payload === undefined) return undefined;
  if (typeof payload === 'string') return payload || undefined;
  if (typeof payload === 'object') {
    if ('detail' in payload) return payload.detail;
    if ('error' in payload) return payload.error;
    if ('message' in payload) return payload.message;
  }
  return undefined;
}

function detailToMessage(detail, status) {
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map(item => {
        const location = Array.isArray(item?.loc) ? item.loc.slice(1).join('.') : '';
        const text = item?.msg || (typeof item === 'string' ? item : '');
        return [location, text].filter(Boolean).join(': ');
      })
      .filter(Boolean);
    if (parts.length) return parts.join('; ');
  }
  if (detail && typeof detail === 'object') {
    if (typeof detail.message === 'string' && detail.message.trim()) return detail.message;
    return JSON.stringify(detail);
  }
  return `Request failed with status ${status}.`;
}

function buildUrl(path, query) {
  if (!hasBackendConfig()) {
    throw new ApiError('API base URL is not configured. Set VITE_API_BASE_URL.', { status: null, detail: 'VITE_API_BASE_URL is not set' });
  }
  const base = getApiBaseUrl();
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const params = new URLSearchParams();
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === '') continue;
      params.set(key, String(value));
    }
  }
  const queryString = params.toString();
  return `${base}${normalizedPath}${queryString ? `?${queryString}` : ''}`;
}

export async function apiFetch(path, { method = 'GET', body, query, fetchImpl, signal } = {}) {
  const url = buildUrl(path, query);
  const fetchFn = fetchImpl ?? globalThis.fetch?.bind(globalThis);
  if (!fetchFn) {
    throw new ApiError('Fetch is not available in this environment.', { status: null, url, method });
  }
  const init = { method, headers: {} };
  if (body !== undefined) {
    init.headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(body);
  }
  if (signal) init.signal = signal;

  let response;
  try {
    response = await fetchFn(url, init);
  } catch (error) {
    throw new ApiError(error?.message || 'Network request failed.', { status: null, detail: error?.message, url, method });
  }

  if (response.status === 204) return null;

  let payload = null;
  const text = await response.text();
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const detail = extractDetail(payload);
    throw new ApiError(detailToMessage(detail, response.status), { status: response.status, detail, url, method });
  }
  return payload;
}
