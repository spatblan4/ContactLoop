import test from 'node:test';
import assert from 'node:assert/strict';

globalThis.localStorage = {
  store: new Map(),
  getItem(key) { return this.store.get(key) ?? null; },
  setItem(key, value) { this.store.set(key, value); },
  removeItem(key) { this.store.delete(key); },
};

const { setApiBaseUrl } = await import('../src/lib/api/client.js');
const {
  askOutreachQuestion,
  askTeacherAssistant,
  getOutreachConversation,
  resetOutreachConversation,
} = await import('../src/lib/api/outreach-plan.js');
const { generateCallSummary } = await import('../src/lib/api/contact-events.js');
const {
  answerReceived,
  conversationFailed,
  createConversationState,
  messageSubmitted,
  normalizeConversationMessages,
} = await import('../src/lib/agent-conversation.js');

setApiBaseUrl('http://localhost:8000');

function jsonResponse(payload, { status = 200 } = {}) {
  return { ok: status >= 200 && status < 300, status, text: async () => JSON.stringify(payload) };
}

test('askOutreachQuestion posts the question and returns the answer', async () => {
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    return jsonResponse({ answer: 'Because of the open follow-up.', candidate_count: 2 });
  };

  const result = await askOutreachQuestion('Why is Emma prioritized today?');

  assert.equal(calls[0].url, 'http://localhost:8000/api/v1/outreach-plan/ask');
  assert.equal(calls[0].init.method, 'POST');
  assert.deepEqual(JSON.parse(calls[0].init.body), { question: 'Why is Emma prioritized today?' });
  assert.equal(result.answer, 'Because of the open follow-up.');
});

test('getOutreachConversation fetches the persisted conversation', async () => {
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    return jsonResponse({
      session_id: 'outreach-qa-1',
      messages: [
        { message_id: 1, role: 'user', text: 'Who should I call first?' },
        { message_id: 2, role: 'assistant', text: 'Start with Emma Johnson.' },
      ],
    });
  };

  const conversation = await getOutreachConversation();

  assert.equal(calls[0].url, 'http://localhost:8000/api/v1/outreach-plan/conversation');
  assert.equal(calls[0].init.method, 'GET');
  assert.equal(conversation.messages.length, 2);
});

test('resetOutreachConversation sends a delete', async () => {
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    return { ok: true, status: 204, text: async () => '' };
  };

  await resetOutreachConversation();

  assert.equal(calls[0].url, 'http://localhost:8000/api/v1/outreach-plan/conversation');
  assert.equal(calls[0].init.method, 'DELETE');
});

test('askTeacherAssistant posts the request', async () => {
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    return jsonResponse({ answer: 'Prioritize Emma Johnson today.', candidate_count: 3 });
  };

  const result = await askTeacherAssistant('What should I prioritize today?');

  assert.equal(calls[0].url, 'http://localhost:8000/api/v1/teacher-assistant/ask');
  assert.equal(calls[0].init.method, 'POST');
  assert.deepEqual(JSON.parse(calls[0].init.body), { request: 'What should I prioritize today?' });
  assert.equal(result.answer, 'Prioritize Emma Johnson today.');
});

test('generateCallSummary posts the contact event id', async () => {
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    return jsonResponse({ note_id: 'note-1', content: 'Summary.', teacher_confirmed: false });
  };

  const result = await generateCallSummary('event-1');

  assert.equal(calls[0].url, 'http://localhost:8000/api/v1/ai/call-summary/generate');
  assert.deepEqual(JSON.parse(calls[0].init.body), { contact_event_id: 'event-1' });
  assert.equal(result.teacher_confirmed, false);
});

test('normalizeConversationMessages maps roles and drops empty texts', () => {
  const messages = normalizeConversationMessages({
    messages: [
      { message_id: 1, role: 'user', text: 'Who should I call first?' },
      { message_id: 2, role: 'assistant', text: 'Start with Emma Johnson.' },
      { message_id: 3, role: 'user', text: '   ' },
    ],
  });

  assert.deepEqual(messages, [
    { role: 'teacher', text: 'Who should I call first?' },
    { role: 'agent', text: 'Start with Emma Johnson.' },
  ]);
  assert.deepEqual(normalizeConversationMessages(null), []);
});

test('conversation state tracks submit, answer, and failure', () => {
  const initial = createConversationState();
  assert.deepEqual(initial, { messages: [], input: '', loading: false, error: null });

  const submitted = messageSubmitted({ ...initial, input: 'Any updates?' }, 'Any updates?');
  assert.equal(submitted.loading, true);
  assert.equal(submitted.input, '');
  assert.deepEqual(submitted.messages, [{ role: 'teacher', text: 'Any updates?' }]);

  const answered = answerReceived(submitted, 'No changes since yesterday.');
  assert.equal(answered.loading, false);
  assert.deepEqual(answered.messages, [
    { role: 'teacher', text: 'Any updates?' },
    { role: 'agent', text: 'No changes since yesterday.' },
  ]);

  const failed = conversationFailed(submitted, 'Outreach Agent is temporarily unavailable.');
  assert.equal(failed.loading, false);
  assert.equal(failed.error, 'Outreach Agent is temporarily unavailable.');
  assert.equal(failed.messages.length, 1);

  const defaultFailure = conversationFailed(submitted, '');
  assert.match(defaultFailure.error, /temporarily unavailable/);
});
