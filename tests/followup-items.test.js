import test from 'node:test';
import assert from 'node:assert/strict';
import { buildFollowUpItems, followUpGroup } from '../src/lib/followup-items.js';

const now = new Date(2026, 7, 25, 12, 0, 0);
const students = [{ id: 'ava', name: 'Ava Chen', relation: 'Dad' }];
const events = [
  { id: '1', studentId: 'ava', result: 'No Answer', attemptNumber: 3, callTime: '2026-08-25T11:18:00-07:00' },
  { id: '2', studentId: 'ava', result: 'No Answer', attemptNumber: 2, callTime: '2026-08-24T11:18:00-07:00' },
  { id: '3', studentId: 'ava', result: 'Connected', attemptNumber: 1, callTime: '2026-08-23T11:18:00-07:00' },
];

test('follow-up items aggregate one open task per student and parent', () => {
  const items = buildFollowUpItems({
    followUps: [
      { id: 'open-1', student_id: 'ava', guardian_id: 'dad', due_at: '2026-08-27T09:00:00-07:00', status: 'open' },
      { id: 'duplicate', student_id: 'ava', guardian_id: 'dad', due_at: '2026-08-28T09:00:00-07:00', status: 'open' },
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
  assert.equal(followUpGroup('2026-08-24T09:00:00-07:00', now), 'TODAY');
  assert.equal(followUpGroup('2026-08-26T09:00:00-07:00', now), 'TOMORROW');
});

test('connected latest contact removes a stale open follow-up', () => {
  const items = buildFollowUpItems({
    followUps: [{ id: 'stale', student_id: 'ava', guardian_id: 'dad', due_at: '2026-08-27T09:00:00-07:00', status: 'open' }],
    events: [{ studentId: 'ava', guardianId: 'dad', result: 'Connected', callTime: '2026-08-26T11:18:00-07:00' }],
    students,
    now,
  });

  assert.equal(items.length, 0);
});
