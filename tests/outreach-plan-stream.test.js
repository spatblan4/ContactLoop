import test from 'node:test';
import assert from 'node:assert/strict';

globalThis.localStorage = {
  store: new Map(),
  getItem(key) { return this.store.get(key) ?? null; },
  setItem(key, value) { this.store.set(key, value); },
  removeItem(key) { this.store.delete(key); },
};

const { generateOutreachPlanStream } = await import('../src/lib/api/outreach-plan.js');

function sseResponse(chunks, { status = 200 } = {}) {
  const encoder = new TextEncoder();
  let index = 0;
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Map([['content-type', 'text/event-stream; charset=utf-8']]),
    body: {
      getReader() {
        return {
          read: async () =>
            index < chunks.length
              ? { done: false, value: encoder.encode(chunks[index++]) }
              : { done: true, value: undefined },
        };
      },
    },
  };
}

test('generateOutreachPlanStream reports progress and resolves with the plan', async () => {
  localStorage.setItem('contactloop.auth.token', 'token-1');
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    return sseResponse([
      'event: candidates\ndata: {"count":2}\n\n',
      'event: message\ndata: {"role":"assistant","text":"Checking follow-"}\n\n',
      'event: message\ndata: {"role":"assistant","text":"ups."}\n\n',
      'event: plan\ndata: {"source":"agent","generatedAt":"2026-09-12T10:00:00Z","items":[]}\n\n',
    ]);
  };

  const progress = [];
  const plan = await generateOutreachPlanStream(update => progress.push(update));

  assert.equal(calls[0].url, '/api/v1/ai/outreach-plan/generate/stream');
  assert.equal(calls[0].options.headers.Authorization, 'Bearer token-1');
  assert.deepEqual(
    progress.map(update => update.event),
    ['candidates', 'message', 'message'],
  );
  assert.equal(progress[1].data.text, 'Checking follow-');
  assert.equal(plan.source, 'agent');
});

test('generateOutreachPlanStream rejects on the error event', async () => {
  globalThis.fetch = async () =>
    sseResponse([
      'event: candidates\ndata: {"count":1}\n\n',
      'event: error\ndata: {"detail":"Outreach Agent is temporarily unavailable. Try again shortly."}\n\n',
    ]);

  await assert.rejects(
    () => generateOutreachPlanStream(() => {}),
    /temporarily unavailable/,
  );
});

test('generateOutreachPlanStream rejects non-stream responses', async () => {
  globalThis.fetch = async () => ({
    ok: false,
    status: 503,
    headers: new Map([['content-type', 'application/json']]),
  });

  await assert.rejects(
    () => generateOutreachPlanStream(() => {}),
    /temporarily unavailable/,
  );
});
