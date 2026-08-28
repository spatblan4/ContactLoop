import test from 'node:test';
import assert from 'node:assert/strict';
import {
  contextSavedMessage,
  homeEntryForMode,
  studentSelectForMode,
  shouldShowDemoGuide,
} from '../src/lib/app-config.js';

test('saved context only offers an AI update when the provider is enabled', () => {
  assert.deepEqual(contextSavedMessage(false), {
    title: 'New context saved.',
    detail: 'This note is saved with the student record.',
    actionLabel: null,
  });
  assert.deepEqual(contextSavedMessage(true), {
    title: 'New context saved.',
    detail: 'Update the AI Contact Summary with this note?',
    actionLabel: 'Update AI Summary',
  });
});

test('authenticated mode hides the demo guide', () => {
  assert.equal(shouldShowDemoGuide('authenticated'), false);
});

test('demo mode shows the demo guide', () => {
  assert.equal(shouldShowDemoGuide('demo'), true);
});

test('beta mode enters through account authentication, while demo stays guest-accessible', () => {
  assert.deepEqual(homeEntryForMode('authenticated'), {
    primaryAction: 'sign-in',
    primaryLabel: 'Sign in',
    secondaryAction: 'sign-up',
    secondaryLabel: 'Create account',
  });
  assert.deepEqual(homeEntryForMode('demo'), {
    primaryAction: 'demo',
    primaryLabel: 'Try the demo',
    secondaryAction: null,
    secondaryLabel: null,
  });
});

test('demo mode uses only the columns in the demo database schema', () => {
  assert.equal(
    studentSelectForMode('demo'),
    'id, name, initials, accent, guardians(id, name, relation, phone)',
  );
});

test('authenticated mode keeps the richer student fields needed for import and beta', () => {
  assert.equal(
    studentSelectForMode('authenticated'),
    'id, name, first_name, last_name, initials, accent, guardians(id, name, relation, phone, email, preferred_contact_method)',
  );
});
