import test from 'node:test';
import assert from 'node:assert/strict';
import { TwilioTelephonyProvider } from '../src/lib/telephony.js';
import { setApiBaseUrl } from '../src/lib/api/client.js';

test('Twilio provider sends the selected student and topic through FastAPI', async () => {
  const originalFetch = globalThis.fetch;
  const requests = [];
  setApiBaseUrl('http://127.0.0.1:8000');
  globalThis.fetch = async (url, init) => {
    requests.push({ url: String(url), init });
    return new Response(JSON.stringify({ eventId: 'event-1' }), { status: 200 });
  };

  try {
    const result = await new TwilioTelephonyProvider().startCall('student-1', { plannedTopic: 'Behavior' });

    assert.deepEqual(result, { eventId: 'event-1' });
    assert.deepEqual(requests, [{
      url: 'http://127.0.0.1:8000/api/v1/telephony/calls',
      init: {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: 'student-1', planned_topic: 'Behavior' }),
      },
    }]);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('Twilio status sync does not make a global request without an event ID', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => {
    throw new Error('A global status sync must not call the network.');
  };

  try {
    assert.deepEqual(await new TwilioTelephonyProvider().syncCallStatus(), { synced: [] });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('Twilio status sync sends one event ID through FastAPI', async () => {
  const originalFetch = globalThis.fetch;
  const requests = [];
  setApiBaseUrl('http://127.0.0.1:8000');
  globalThis.fetch = async (url, init) => {
    requests.push({ url: String(url), init });
    return new Response(JSON.stringify({ synced: [] }), { status: 200 });
  };

  try {
    assert.deepEqual(await new TwilioTelephonyProvider().syncCallStatus('event-1'), { synced: [] });
    assert.deepEqual(requests, [{
      url: 'http://127.0.0.1:8000/api/v1/telephony/call-status-sync',
      init: {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: 'event-1' }),
      },
    }]);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
