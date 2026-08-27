import test from 'node:test';
import assert from 'node:assert/strict';
import { createVoiceNoteState, canSaveVoiceNote, voiceNoteError } from '../src/lib/voice-note.js';
import { edgeFunctionError } from '../src/lib/edge-errors.js';

test('voice note starts idle and only becomes reviewable after transcript', () => {
  assert.deepEqual(createVoiceNoteState(), { status: 'idle', elapsedSeconds: 0, transcript: '', error: null });
  assert.equal(canSaveVoiceNote({ status: 'review', transcript: '  Mom asked about homework.  ' }), true);
  assert.equal(canSaveVoiceNote({ status: 'transcribing', transcript: 'Mom asked about homework.' }), false);
});

test('voice note errors are retryable and do not become saveable', () => {
  const state = voiceNoteError('Transcription failed');
  assert.deepEqual(state, { status: 'error', elapsedSeconds: 0, transcript: '', error: 'Transcription failed' });
  assert.equal(canSaveVoiceNote(state), false);
});

test('edge function network failures explain the likely browser configuration problem', () => {
  assert.equal(
    edgeFunctionError(new TypeError('Failed to fetch'), 'create-voice-upload'),
    'create-voice-upload could not be reached. Check the function URL and CORS allowed origin.',
  );
});
