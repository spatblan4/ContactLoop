import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { setApiBaseUrl } from '../src/lib/api/client.js';
import { generateOutreachPlan } from '../src/lib/api/outreach-plan.js';
import { normalizeOutreachPlan } from '../src/lib/outreach-plan.js';

setApiBaseUrl('http://localhost:8000');

const here = dirname(fileURLToPath(import.meta.url));
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
    await run();
    return requests[0];
  } finally {
    globalThis.fetch = originalFetch;
  }
}

test('outreach plan client posts to the protected FastAPI route', async () => {
  const request = await withMockFetch(
    () => jsonResponse(200, { generated_at: '2026-09-06T00:00:00Z', source: 'agent', items: [] }),
    () => generateOutreachPlan(),
  );
  assert.equal(request.url, 'http://localhost:8000/api/v1/ai/outreach-plan/generate');
  assert.equal(request.init.method, 'POST');
});

test('plan normalization retains only valid ranked recommendations', () => {
  assert.equal(
    normalizeOutreachPlan({ items: [{ student_id: 's1', priority: 'high', reason: 'Open follow-up is due.', suggested_next_step: 'Call today.' }] }).items[0].priority,
    'high',
  );
});

test('plan normalization rejects malformed recommendation fields', () => {
  assert.throws(
    () => normalizeOutreachPlan({ items: [{ student_id: 's1', priority: 'urgent', reason: '', suggested_next_step: 'Call today.' }] }),
    /priority|reason/i,
  );
});

test('dashboard source contains an agent refresh action and no automatic follow-up write', () => {
  const source = readFileSync(join(here, '../src/app.js'), 'utf8');
  assert.match(source, /Refresh with Agent/);
  assert.match(source, /Review/);
  assert.match(source, /Create follow-up/);
  assert.doesNotMatch(source, /generateOutreachPlan\([^]*createFollowUp/);
});
