import test from 'node:test';
import assert from 'node:assert/strict';
import { buildMeetingBrief } from '../src/lib/meeting-brief.js';

const now = new Date(2026, 7, 25, 12);
const students = [{ id: 'emma', name: 'Emma Johnson', relation: 'Mom', parent: 'Sarah Johnson' }];
const events = [
  { id: '1', studentId: 'emma', result: 'No Answer', callTime: '2026-08-22T10:00:00-07:00', duration: null, topic: null, note: null, followUpId: 'f1' },
  { id: '2', studentId: 'emma', result: 'Connected', callTime: '2026-08-25T14:00:00-07:00', duration: '7m 43s', topic: 'IEP', note: 'Parent confirmed Friday meeting and asked for transportation information.', followUpId: null },
];

test('meeting brief computes overview from real events and topics', () => {
  const brief = buildMeetingBrief({ events, students, followUps: [{ id: 'f1', student_id: 'emma', due_at: '2026-08-27T09:00:00-07:00', status: 'open' }], studentId: 'emma', range: { preset: 'this-month' }, now });
  assert.deepEqual(brief.overview, { totalAttempts: 2, successfulConversations: 1, noAnswer: 1, busy: 0, failed: 0, lastSuccessfulContact: 'Aug 25, 2026', openFollowUps: 1 });
  assert.deepEqual(brief.topics, [{ label: 'IEP', count: 1 }]);
  assert.match(brief.concerns[0], /transportation/);
  assert.match(brief.agreements[0], /confirmed/);
});

test('meeting brief detailed history keeps notes and never exposes phone or provider data', () => {
  const brief = buildMeetingBrief({ events, students, followUps: [], studentId: 'emma', range: { preset: 'this-month' }, now });
  assert.equal(brief.detailedHistory.length, 2);
  assert.equal(brief.detailedHistory[0].note.includes('Friday'), true);
  assert.equal('providerCallId' in brief.detailedHistory[0], false);
});
