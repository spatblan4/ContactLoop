import test from 'node:test';
import assert from 'node:assert/strict';
import { getDashboardInsights } from '../src/lib/dashboard-insights.js';

const now = new Date(2026, 7, 25, 12, 0, 0);
const students = [
  { id: 'emma', name: 'Emma Johnson' },
  { id: 'ava', name: 'Ava Chen' },
  { id: 'noah', name: 'Noah Williams' },
  { id: 'lucas', name: 'Lucas Smith' },
];

const events = [
  { id: '1', studentId: 'emma', result: 'No Answer', attemptNumber: 2, callTime: '2026-08-25T10:32:00-07:00', topic: 'Progress' },
  { id: '2', studentId: 'ava', result: 'Failed', attemptNumber: 1, callTime: '2026-08-25T09:15:00-07:00', topic: 'Scheduling' },
  { id: '4', studentId: 'lucas', result: 'Connected', attemptNumber: 1, callTime: '2026-08-25T08:00:00-07:00', topic: 'IEP' },
  { id: '5', studentId: 'lucas', result: 'Initiated', attemptNumber: 2, callTime: '2026-08-25T08:30:00-07:00', topic: null },
];

test('dashboard insights use final outcomes and exclude pending calls', () => {
  const insights = getDashboardInsights({ events, students, followUps: [{ id: 'follow-1', student_id: 'ava', due_at: '2026-08-25T09:00:00-07:00', status: 'open' }], now });

  assert.deepEqual(insights.metrics, { callAttempts: 3, connected: 1, unsuccessful: 2, followUpsDue: 1 });
  assert.equal(insights.needsFollowUp.find(item => item.student.id === 'lucas'), undefined);
  assert.equal(insights.needsFollowUp.find(item => item.student.id === 'emma').label, 'No answer · Attempt #2');
  assert.equal(insights.needsFollowUp.find(item => item.student.id === 'ava').label, 'Follow-up due today');
  assert.equal(insights.needsFollowUp.find(item => item.student.id === 'noah').label, 'No successful parent contact this week');
});

test('weekly brief aggregates successful contacts and topics', () => {
  const insights = getDashboardInsights({ events, students, followUps: [], now });

  assert.deepEqual(insights.weekBrief, {
    totalAttempts: 3,
    successfulContacts: 1,
    studentsNeedingFollowUp: 3,
    topTopics: [
      { label: 'IEP', count: 1 },
    ],
  });
});
