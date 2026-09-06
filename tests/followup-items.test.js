import test from 'node:test';
import assert from 'node:assert/strict';
import { buildFollowUpItems, followUpGroup } from '../src/lib/followup-items.js';

const now = new Date(2026, 7, 25, 12, 0, 0);
const localISO = (month, day, hour, minute = 0) => new Date(2026, month - 1, day, hour, minute).toISOString();
const students = [{ id: 'ava', name: 'Ava Chen', relation: 'Dad' }];
const events = [
  { id: '1', studentId: 'ava', result: 'No Answer', attemptNumber: 3, callTime: localISO(8, 25, 11, 18) },
  { id: '2', studentId: 'ava', result: 'No Answer', attemptNumber: 2, callTime: localISO(8, 24, 11, 18) },
  { id: '3', studentId: 'ava', result: 'Connected', attemptNumber: 1, callTime: localISO(8, 23, 11, 18) },
];

test('follow-up items aggregate one open task per student and parent', () => {
  const items = buildFollowUpItems({
    followUps: [
      { id: 'open-1', student_id: 'ava', guardian_id: 'dad', due_at: localISO(8, 27, 9, 0), status: 'open' },
      { id: 'duplicate', student_id: 'ava', guardian_id: 'dad', due_at: localISO(8, 28, 9, 0), status: 'open' },
    ],
    events,
    students,
    now,
  });

  assert.equal(items.length, 1);
  assert.equal(items[0].summary, '2 unsuccessful attempts');
  assert.equal(items[0].lastResult, 'No Answer');
  assert.equal(items[0].attemptNumber, 3);
  assert.equal(items[0].nextFollowUp, 'Aug 27 · 9:00 AM');
  assert.equal(followUpGroup(items[0].dueAt, now), 'UPCOMING');
});

test('overdue follow-ups are prioritized in TODAY', () => {
  assert.equal(followUpGroup(localISO(8, 24, 9, 0), now), 'TODAY');
  assert.equal(followUpGroup(localISO(8, 26, 9, 0), now), 'TOMORROW');
});

test('connected latest contact removes a stale open follow-up', () => {
  const items = buildFollowUpItems({
    followUps: [{ id: 'stale', student_id: 'ava', guardian_id: 'dad', due_at: localISO(8, 27, 9, 0), status: 'open' }],
    events: [{ studentId: 'ava', guardianId: 'dad', result: 'Connected', callTime: localISO(8, 26, 11, 18) }],
    students,
    now,
  });

  assert.equal(items.length, 0);
});
