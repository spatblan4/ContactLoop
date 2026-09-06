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

export function contextSavedMessage(aiEnabled) {
  if (!aiEnabled) {
    return {
      title: 'New context saved.',
      detail: 'This note is saved with the student record.',
      actionLabel: null,
    };
  }

  return {
    title: 'New context saved.',
    detail: 'Update the AI Contact Summary with this note?',
    actionLabel: 'Update AI Summary',
  };
}

export const CONFIGURED_TEACHER_NAME = String(import.meta.env?.VITE_TEACHER_NAME || '').trim();

function initialsFromName(name) {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return 'T';
  return parts.slice(0, 2).map(part => part[0].toUpperCase()).join('');
}

function nameFromEmail(email) {
  const localPart = String(email || '').split('@')[0];
  const words = localPart.split(/[._\-+]+/).filter(word => /[a-zA-Z]/.test(word));
  if (!words.length) return '';
  return words.map(word => word[0].toUpperCase() + word.slice(1).toLowerCase()).join(' ');
}

export function teacherProfile({ session, appMode = APP_MODE, teacherName = CONFIGURED_TEACHER_NAME } = {}) {
  const configured = String(teacherName || '').trim();
  const email = session?.user?.email || '';
  const name = configured || nameFromEmail(email) || (appMode === 'demo' ? 'Demo Teacher' : 'Teacher');
  const subtitle = configured
    ? (appMode === 'demo' ? 'Demo workspace' : 'ContactLoop workspace')
    : email || (appMode === 'demo' ? 'Demo workspace' : 'Special education');
  return { name, initials: initialsFromName(name), subtitle };
}
