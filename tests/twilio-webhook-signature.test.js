import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import test from 'node:test';

const signatureModuleUrl = new URL(
  '../supabase/functions/twilio-webhook/twilio-signature.js',
  import.meta.url,
);

test('Twilio webhook signatures accept authentic form posts and reject tampering', async () => {
  const { validateTwilioSignature = async () => false } = await import(signatureModuleUrl).catch(() => ({}));
  const url = 'https://example.com/twilio-webhook?event_id=event-123';
  const authToken = 'test-auth-token';
  const formData = new FormData();
  formData.append('CallStatus', 'completed');
  formData.append('CallSid', 'CA123');
  formData.append('CallDuration', '12');

  const payload = `${url}CallDuration12CallSidCA123CallStatuscompleted`;
  const signature = createHmac('sha1', authToken).update(payload).digest('base64');

  assert.equal(await validateTwilioSignature({ url, formData, signature, authToken }), true);
  formData.set('CallDuration', '99');
  assert.equal(await validateTwilioSignature({ url, formData, signature, authToken }), false);
});
