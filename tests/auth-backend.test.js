import test from 'node:test';
import assert from 'node:assert/strict';
import { apiFetch, setApiBaseUrl, API_PREFIX } from '../src/lib/api/client.js';
import { getStoredToken, setStoredToken, clearStoredToken } from '../src/lib/api/auth-token.js';
import * as backendAuth from '../src/lib/api/auth.js';
import { getAuthSession, signInWithPassword, signUpWithPassword, subscribeToAuthChanges } from '../src/lib/auth.js';

setApiBaseUrl('http://localhost:8000');

const jsonResponse = (status, payload) => ({
  ok: status >= 200 && status < 300,
  status,
  text: async () => JSON.stringify(payload),
});

async function withMockFetch(handler, run) {
  const originalFetch = globalThis.fetch;
  const requests = [];
  globalThis.fetch = async (url, init) => {
    const request = { url: String(url), init };
    requests.push(request);
    return handler(request);
  };
  try {
    return { result: await run(), requests };
  } finally {
    globalThis.fetch = originalFetch;
  }
}

test('token storage round trips and clears', () => {
  clearStoredToken();
  assert.equal(getStoredToken(), null);
  setStoredToken('token-123');
  assert.equal(getStoredToken(), 'token-123');
  clearStoredToken();
  assert.equal(getStoredToken(), null);
});

test('register stores the token and returns the user', async () => {
  clearStoredToken();
  const { result, requests } = await withMockFetch(
    () => jsonResponse(201, { user: { id: 'u1', email: 'a@b.com', name: 'A' }, token: 'tok-1' }),
    () => backendAuth.register({ email: 'a@b.com', password: 'secret1' }),
  );
  assert.equal(requests[0].url, `http://localhost:8000${API_PREFIX}/auth/register`);
  assert.equal(requests[0].init.method, 'POST');
  assert.deepEqual(JSON.parse(requests[0].init.body), { email: 'a@b.com', password: 'secret1', name: null });
  assert.equal(result.id, 'u1');
  assert.equal(getStoredToken(), 'tok-1');
  clearStoredToken();
});

test('login stores the token and returns the user', async () => {
  clearStoredToken();
  const { result, requests } = await withMockFetch(
    () => jsonResponse(200, { user: { id: 'u2', email: 'x@y.com' }, token: 'tok-2' }),
    () => backendAuth.login({ email: 'x@y.com', password: 'secret2' }),
  );
  assert.equal(requests[0].url, `http://localhost:8000${API_PREFIX}/auth/login`);
  assert.equal(result.email, 'x@y.com');
  assert.equal(getStoredToken(), 'tok-2');
  clearStoredToken();
});

test('fetchMe returns null on failure without throwing', async () => {
  clearStoredToken();
  const { result } = await withMockFetch(
    () => jsonResponse(401, { detail: 'a valid bearer token is required' }),
    () => backendAuth.fetchMe(),
  );
  assert.equal(result, null);
});

test('logout revokes and clears the token even when the request fails', async () => {
  setStoredToken('tok-3');
  await withMockFetch(
    () => jsonResponse(500, { detail: 'boom' }),
    () => backendAuth.logout().catch(() => {}),
  );
  assert.equal(getStoredToken(), null);
});

test('client attaches the stored bearer token to requests', async () => {
  setStoredToken('tok-4');
  const { requests } = await withMockFetch(
    () => jsonResponse(200, []),
    () => apiFetch(`${API_PREFIX}/students`),
  );
  assert.equal(requests[0].init.headers.Authorization, 'Bearer tok-4');
  clearStoredToken();
});

test('client omits the authorization header without a token', async () => {
  clearStoredToken();
  const { requests } = await withMockFetch(
    () => jsonResponse(200, []),
    () => apiFetch(`${API_PREFIX}/students`),
  );
  assert.equal(requests[0].init.headers.Authorization, undefined);
});

test('signInWithPassword returns a supabase-shaped session', async () => {
  clearStoredToken();
  const { result } = await withMockFetch(
    () => jsonResponse(200, { user: { id: 'u9', email: 'z@z.com', name: 'Zed' }, token: 'tok-9' }),
    () => signInWithPassword('z@z.com', 'secret9'),
  );
  assert.equal(result.error, null);
  assert.equal(result.data.session.user.id, 'u9');
  assert.equal(result.data.session.user.email, 'z@z.com');
  clearStoredToken();
});

test('signInWithPassword surfaces login failures as errors', async () => {
  clearStoredToken();
  const { result } = await withMockFetch(
    () => jsonResponse(401, { detail: 'invalid email or password' }),
    () => signInWithPassword('z@z.com', 'wrong'),
  );
  assert.equal(result.data.session, null);
  assert.match(result.error.message, /invalid email or password/);
});

test('signUpWithPassword registers through the backend and returns a session', async () => {
  clearStoredToken();
  const { result, requests } = await withMockFetch(
    () => jsonResponse(201, { user: { id: 'u10', email: 'new@z.com' }, token: 'tok-10' }),
    () => signUpWithPassword('new@z.com', 'secret10'),
  );
  assert.equal(requests[0].url, `http://localhost:8000${API_PREFIX}/auth/register`);
  assert.equal(result.error, null);
  assert.equal(result.data.session.user.id, 'u10');
  clearStoredToken();
});

test('getAuthSession resolves the session from /auth/me', async () => {
  setStoredToken('tok-11');
  const { result, requests } = await withMockFetch(
    () => jsonResponse(200, { id: 'u11', email: 'me@z.com', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' }),
    () => getAuthSession(),
  );
  assert.equal(requests[0].url, `http://localhost:8000${API_PREFIX}/auth/me`);
  assert.equal(requests[0].init.headers.Authorization, 'Bearer tok-11');
  assert.equal(result.user.email, 'me@z.com');
  clearStoredToken();
});

test('subscribeToAuthChanges returns an unsubscribe handle', () => {
  const subscription = subscribeToAuthChanges(() => {});
  assert.equal(typeof subscription.unsubscribe, 'function');
});
