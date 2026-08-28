import test from 'node:test';
import assert from 'node:assert/strict';
import { TwilioTelephonyProvider } from '../src/lib/telephony.js';

test('Twilio provider forwards the planned topic when starting a call', async () => {
  const calls = [];
  const client = {
    functions: {
      async invoke(name, options) {
        calls.push({ name, options });
        return { data: { eventId: 'event-1' }, error: null };
      },
    },
  };

  const provider = new TwilioTelephonyProvider(client);
  await provider.startCall('student-1', { plannedTopic: 'Behavior' });

  assert.deepEqual(calls, [{
    name: 'start-call',
    options: { body: { studentId: 'student-1', plannedTopic: 'Behavior' } },
  }]);
});

