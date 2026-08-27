import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const sourceUrl = new URL('../supabase/functions/start-call/index.ts', import.meta.url);

test('Twilio trial calls use only the supported template and callback parameters', async () => {
  const source = await readFile(sourceUrl, 'utf8');

  assert.match(
    source,
    /Url:\s*'https:\/\/webhooks\.twilio\.com\/v1\/Voice\/Template\/voice_text_to_speech'/,
    'trial calls must use a Twilio-provided Voice template URL',
  );
  assert.doesNotMatch(source, /\bTwiml:/, 'inline TwiML is disallowed for this trial API request');
  assert.doesNotMatch(source, /\bStatusCallbackMethod:/, 'trial calls must use the callback default');
  assert.doesNotMatch(source, /StatusCallbackEvent/, 'trial calls must use the default completed callback');
});
