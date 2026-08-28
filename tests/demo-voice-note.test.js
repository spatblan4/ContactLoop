import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemoVoiceNote, addDemoTeacherNote } from '../src/lib/demo-voice-note.js';

test('demo voice note produces a teacher-reviewable local transcript', () => {
  const note = createDemoVoiceNote();
  assert.equal(note.status, 'review');
  assert.equal(note.source, 'voice');
  assert.match(note.transcript, /demo/i);
});

test('demo voice note adds a local teacher note without a backend call', () => {
  const notes = addDemoTeacherNote([], 'student-1', 'Parent shared an update.');
  assert.equal(notes.length, 1);
  assert.equal(notes[0].studentId, 'student-1');
  assert.equal(notes[0].content, 'Parent shared an update.');
  assert.equal(notes[0].source, 'voice');
});
