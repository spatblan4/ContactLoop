import test from 'node:test';
import assert from 'node:assert/strict';
import { isAuthenticatedMode, resolveAppMode } from '../src/lib/app-config.js';
import { getAuthSession, sendEmailOtp, signInWithPassword, signUpWithPassword, signOut, verifyEmailOtp } from '../src/lib/auth.js';

test('runtime mode defaults to demo and only accepts authenticated explicitly', () => {
  assert.equal(resolveAppMode(), 'demo');
  assert.equal(resolveAppMode('demo'), 'demo');
  assert.equal(resolveAppMode('authenticated'), 'authenticated');
  assert.equal(isAuthenticatedMode('authenticated'), true);
  assert.equal(isAuthenticatedMode('demo'), false);
});

test('auth helpers delegate to the supplied Supabase auth client', async () => {
  const calls = [];
  const client = {
    auth: {
      getSession: async () => ({ data: { session: { user: { id: 'teacher-1' } } }, error: null }),
      signInWithPassword: async credentials => { calls.push(['signIn', credentials]); return { data: { user: { id: 'teacher-1' } }, error: null }; },
      signUp: async credentials => { calls.push(['signUp', credentials]); return { data: { user: { id: 'teacher-1' } }, error: null }; },
      signInWithOtp: async credentials => { calls.push(['sendOtp', credentials]); return { data: {}, error: null }; },
      verifyOtp: async credentials => { calls.push(['verifyOtp', credentials]); return { data: { session: { user: { id: 'teacher-1' } } }, error: null }; },
      signOut: async () => { calls.push(['signOut']); return { error: null }; },
    },
  };
  assert.deepEqual(await getAuthSession(client), { user: { id: 'teacher-1' } });
  await signInWithPassword('teacher@example.com', 'password', client);
  await signUpWithPassword('teacher@example.com', 'password', client);
  await sendEmailOtp('teacher@example.com', client, 'http://localhost:5175');
  await verifyEmailOtp('teacher@example.com', '123456', client);
  await signOut(client);
  assert.deepEqual(calls, [
    ['signIn', { email: 'teacher@example.com', password: 'password' }],
    ['signUp', { email: 'teacher@example.com', password: 'password' }],
    ['sendOtp', { email: 'teacher@example.com', options: { shouldCreateUser: false, emailRedirectTo: 'http://localhost:5175' } }],
    ['verifyOtp', { email: 'teacher@example.com', token: '123456', type: 'email' }],
    ['signOut'],
  ]);
});
