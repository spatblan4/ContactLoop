import test from 'node:test';
import assert from 'node:assert/strict';
import { filterContactLogEvents, toContactLogCsv } from '../src/lib/contact-log.js';
import { cycleAttemptNumber, nextAttemptNumber } from '../src/lib/contact-attempts.js';

const now = new Date(2026, 7, 25, 12);
const students = [
  { id: 'emma', name: 'Emma Johnson', parent: 'Sarah Johnson', relation: 'Mom' },
  { id: 'ava', name: 'Ava Chen', parent: 'Michael Chen', relation: 'Dad' },
];
const events = [
  { id: '1', studentId: 'emma', guardianId: 'mom', result: 'No Answer', callTime: '2026-08-22T10:00:00-07:00', duration: null, topic: null, attemptNumber: 1 },
  { id: '2', studentId: 'emma', guardianId: 'mom', result: 'Busy', callTime: '2026-08-23T10:00:00-07:00', duration: null, topic: 'IEP', attemptNumber: 2 },
  { id: '3', studentId: 'emma', guardianId: 'mom', result: 'Connected', callTime: '2026-08-25T10:00:00-07:00', duration: '9 sec', topic: 'Progress', attemptNumber: 3 },
  { id: '4', studentId: 'ava', guardianId: 'dad', result: 'Failed', callTime: '2026-08-25T11:00:00-07:00', duration: null, topic: null, attemptNumber: 1 },
];

test('contact log filters by search, date, outcome, and student', () => {
  const filtered = filterContactLogEvents(events, { search: 'sarah', range: { preset: 'this-month' }, outcome: 'Connected', studentId: 'all' }, students, now);
  assert.deepEqual(filtered.map(event => event.id), ['3']);
});

test('contact log CSV contains only the supplied filtered rows and separates topics', () => {
  const csv = toContactLogCsv([events[2]], students);
  assert.match(csv, /Student,Parent,When,Outcome,Duration,Planned Topic,Discussed Topics,Attempt/);
  assert.match(csv, /Emma Johnson,Sarah Johnson/);
  assert.match(csv, /Progress/);
  assert.doesNotMatch(csv, /Ava Chen/);
});

test('attempt numbers reset after a connected contact', () => {
  assert.equal(cycleAttemptNumber(events, events[0]), 1);
  assert.equal(cycleAttemptNumber(events, events[1]), 2);
  assert.equal(cycleAttemptNumber(events, events[2]), 3);
  assert.equal(nextAttemptNumber(events, 'emma', 'mom'), 1);
  assert.equal(nextAttemptNumber(events, 'ava', 'dad'), 2);
});
