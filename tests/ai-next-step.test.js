import test from 'node:test';
import assert from 'node:assert/strict';
import { groundBriefNextStep } from '../src/lib/ai-next-step.js';

test('fills a missing AI next step from the earliest open follow-up for the student', () => {
  const brief = groundBriefNextStep({
    brief: { key_topics: [], suggested_next_step: 'No suggested next step recorded.' },
    studentId: 'student-1',
    followUps: [
      { studentId: 'student-1', dueAt: '2026-09-22T16:00:00Z', status: 'open' },
      { studentId: 'student-2', dueAt: '2026-09-14T16:00:00Z', status: 'open' },
      { studentId: 'student-1', dueAt: '2026-09-15T16:00:00Z', status: 'open' },
    ],
  });

  assert.equal(brief.suggested_next_step, 'Follow up with the parent on Tuesday, September 15, 2026.');
});

test('preserves a substantive suggestion returned by the agent', () => {
  const brief = groundBriefNextStep({
    brief: { suggested_next_step: 'Share the confirmed reading resources.' },
    studentId: 'student-1',
    followUps: [{ studentId: 'student-1', dueAt: '2026-09-15T16:00:00Z', status: 'open' }],
  });

  assert.equal(brief.suggested_next_step, 'Share the confirmed reading resources.');
});
