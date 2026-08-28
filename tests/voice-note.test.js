import test from 'node:test';
import assert from 'node:assert/strict';
import { createVoiceNoteState, canSaveVoiceNote, voiceNoteError } from '../src/lib/voice-note.js';
import { edgeFunctionError } from '../src/lib/edge-errors.js';
import { notesForStudent, teacherNoteSourceLabel, normalizeTeacherNote } from '../src/lib/teacher-notes.js';
import { createAiItemDialogState, aiItemLabel } from '../src/lib/ai-item-dialog.js';

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

test('Supabase request failures are translated into a useful retry message', () => {
  assert.equal(
    edgeFunctionError(new Error('Failed to send a request to the Edge Function'), 'Voice note service'),
    'Voice note service could not be reached. Check the function URL and CORS allowed origin.',
  );
});

test('teacher notes are limited to the student and shown newest first', () => {
  const notes = notesForStudent([
    { student_id: 'emma', content: 'older', created_at: '2026-08-25T09:00:00Z' },
    { student_id: 'lucas', content: 'other student', created_at: '2026-08-26T09:00:00Z' },
    { student_id: 'emma', content: 'newer', created_at: '2026-08-26T10:00:00Z' },
  ], 'emma');

  assert.deepEqual(notes.map(note => note.content), ['newer', 'older']);
});

test('teacher note source labels explain how context was added', () => {
  assert.equal(teacherNoteSourceLabel('voice'), 'Voice note');
  assert.equal(teacherNoteSourceLabel('typed'), 'Typed note');
});

test('database teacher notes are normalized for the detail view', () => {
  assert.deepEqual(normalizeTeacherNote({
    id: 'note-1',
    student_id: 'emma',
    content: 'Parent asked about homework.',
    source: 'voice',
    teacher_confirmed: true,
    created_at: '2026-08-26T10:00:00Z',
  }), {
    id: 'note-1',
    studentId: 'emma',
    content: 'Parent asked about homework.',
    source: 'voice',
    teacherConfirmed: true,
    createdAt: '2026-08-26T10:00:00Z',
  });
});

test('AI add-item dialog keeps the field in app state instead of using a browser prompt', () => {
  assert.deepEqual(createAiItemDialogState('recorded_resolutions'), {
    step: 'ai-add-item',
    field: 'recorded_resolutions',
    value: '',
    error: null,
  });
  assert.equal(aiItemLabel('recorded_resolutions'), 'Recorded resolution');
});
