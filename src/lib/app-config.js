export function resolveAppMode(value) {
  return value === 'authenticated' ? 'authenticated' : 'demo';
}

export const APP_MODE = resolveAppMode(import.meta.env?.VITE_APP_MODE);
export const AUTH_REQUIRED = APP_MODE === 'authenticated';

export function shouldShowDemoGuide(mode = APP_MODE) {
  return resolveAppMode(mode) === 'demo';
}

export const SHOW_DEMO_GUIDE = shouldShowDemoGuide();

export function isAuthenticatedMode(mode = APP_MODE) {
  return resolveAppMode(mode) === 'authenticated';
}

export function studentSelectForMode(mode = APP_MODE) {
  if (!isAuthenticatedMode(mode)) {
    return 'id, name, initials, accent, guardians(id, name, relation, phone)';
  }
  return 'id, name, first_name, last_name, initials, accent, guardians(id, name, relation, phone, email, preferred_contact_method)';
}

export function homeEntryForMode(mode = APP_MODE) {
  if (isAuthenticatedMode(mode)) {
    return {
      primaryAction: 'sign-in',
      primaryLabel: 'Sign in',
      secondaryAction: 'sign-up',
      secondaryLabel: 'Create account',
    };
  }

  return {
    primaryAction: 'demo',
    primaryLabel: 'Try the demo',
    secondaryAction: null,
    secondaryLabel: null,
  };
}
