import test from 'node:test';
import assert from 'node:assert/strict';
import { AwsStrandsContactBriefProvider, createContactBriefProvider } from '../src/lib/ai-provider.js';

test('AWS provider sends only the selected student and date range', async () => {
  let request;
  const provider = new AwsStrandsContactBriefProvider({
    endpoint: 'https://ai.example.test/',
    fetchImpl: async (url, options) => { request = { url, options }; return new Response('{"brief":{}}', { status: 200 }); },
  });
  await provider.generate({ studentId: 'emma', dateFrom: '2026-08-01T00:00:00Z', dateTo: '2026-09-01T00:00:00Z' });
  assert.equal(request.url, 'https://ai.example.test/contact-brief');
  assert.deepEqual(JSON.parse(request.options.body), { student_id: 'emma', date_from: '2026-08-01T00:00:00Z', date_to: '2026-09-01T00:00:00Z', include_notes: true });
});

test('provider factory keeps an explicit non-AI provider available', () => {
  assert.equal(createContactBriefProvider({ provider: 'none' }).constructor.name, 'ContactBriefProvider');
  assert.equal(createContactBriefProvider({ provider: 'aws-strands-bedrock', endpoint: 'https://ai.example.test' }).constructor.name, 'AwsStrandsContactBriefProvider');
});

test('AWS provider binds the browser fetch context', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async function fetchWithWindowContext(url, options) {
    assert.equal(this, globalThis);
    return new Response('{"brief":{}}', { status: 200 });
  };
  try {
    const provider = new AwsStrandsContactBriefProvider({ endpoint: 'https://ai.example.test' });
    await provider.generate({ studentId: 'emma', dateFrom: '2026-08-01', dateTo: '2026-09-01' });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('AWS provider includes a safe backend error detail', async () => {
  const provider = new AwsStrandsContactBriefProvider({
    endpoint: 'https://ai.example.test',
    fetchImpl: async () => new Response(JSON.stringify({ error: 'Bedrock access denied' }), { status: 502 }),
  });
  await assert.rejects(
    provider.generate({ studentId: 'emma', dateFrom: '2026-08-01', dateTo: '2026-09-01' }),
    { message: 'AWS Contact Brief provider failed (502): Bedrock access denied' },
  );
});
