import test from 'node:test';
import assert from 'node:assert/strict';
import { buildContactSummaryStats } from '../src/lib/contact-summary.js';

test('contact summary stats count final outcomes for one student', () => {
  const stats = buildContactSummaryStats({
    studentId: 'ava',
    events: [
      { studentId: 'ava', result: 'No Answer' },
      { studentId: 'ava', result: 'Connected' },
      { studentId: 'ava', result: 'Failed' },
      { studentId: 'lucas', result: 'Connected' },
      { studentId: 'ava', result: 'initiated' },
    ],
    followUps: [{ studentId: 'ava', status: 'open' }, { studentId: 'ava', status: 'completed' }],
  });

  assert.deepEqual(stats, { attempts: 3, connected: 1, unsuccessful: 2, openFollowUps: 1 });
});
