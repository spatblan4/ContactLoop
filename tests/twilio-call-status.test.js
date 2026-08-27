import assert from 'node:assert/strict';
import test from 'node:test';

const statusModuleUrl = new URL(
  '../supabase/functions/sync-call-status/twilio-call-status.js',
  import.meta.url,
);

test('Twilio call states map to ContactLoop outcomes and timestamps', async () => {
  const { contactEventUpdatesFromTwilioCall = () => ({}) } = await import(statusModuleUrl).catch(() => ({}));
  const completed = contactEventUpdatesFromTwilioCall({
    sid: 'CA123',
    status: 'completed',
    duration: '18',
    start_time: 'Tue, 25 Aug 2026 21:00:00 +0000',
    end_time: 'Tue, 25 Aug 2026 21:00:18 +0000',
  });

  assert.deepEqual(completed, {
    provider_call_id: 'CA123',
    provider_status: 'completed',
    result: 'Connected',
    duration_seconds: 18,
    started_at: '2026-08-25T21:00:00.000Z',
    ended_at: '2026-08-25T21:00:18.000Z',
  });

  assert.deepEqual(contactEventUpdatesFromTwilioCall({ sid: 'CA456', status: 'no-answer' }), {
    provider_call_id: 'CA456',
    provider_status: 'no-answer',
    result: 'No Answer',
  });
  assert.deepEqual(contactEventUpdatesFromTwilioCall({ sid: 'CA789', status: 'in-progress' }), {
    provider_call_id: 'CA789',
    provider_status: 'in-progress',
    result: 'Connected',
  });
});
