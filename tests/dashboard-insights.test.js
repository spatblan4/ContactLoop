import test from 'node:test';
import assert from 'node:assert/strict';
import { getDashboardInsights } from '../src/lib/dashboard-insights.js';

const now = new Date(2026, 7, 25, 12, 0, 0);
const localISO = (month, day, hour, minute = 0) => new Date(2026, month - 1, day, hour, minute).toISOString();
const students = [
  { id: 'emma', name: 'Emma Johnson' },
  { id: 'ava', name: 'Ava Chen' },
  { id: 'noah', name: 'Noah Williams' },
  { id: 'lucas', name: 'Lucas Smith' },
];

const events = [
  { id: '1', studentId: 'emma', result: 'No Answer', attemptNumber: 2, callTime: localISO(8, 25, 10, 32), topic: 'Progress' },
  { id: '2', studentId: 'ava', result: 'Failed', attemptNumber: 1, callTime: localISO(8, 25, 9, 15), topic: 'Scheduling' },
  { id: '4', studentId: 'lucas', result: 'Connected', attemptNumber: 1, callTime: localISO(8, 25, 8, 0), topic: 'IEP' },
  { id: '5', studentId: 'lucas', result: 'Initiated', attemptNumber: 2, callTime: localISO(8, 25, 8, 30), topic: null },
];

test('dashboard insights use final outcomes and exclude pending calls', () => {
  const insights = getDashboardInsights({ events, students, followUps: [{ id: 'follow-1', student_id: 'ava', due_at: localISO(8, 25, 9, 0), status: 'open' }], now });

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
