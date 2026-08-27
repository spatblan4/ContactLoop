export function resolveAppMode(value) {
  return value === 'authenticated' ? 'authenticated' : 'demo';
}

export const APP_MODE = resolveAppMode(import.meta.env?.VITE_APP_MODE);
export const AUTH_REQUIRED = APP_MODE === 'authenticated';

export function isAuthenticatedMode(mode = APP_MODE) {
  return resolveAppMode(mode) === 'authenticated';
}
