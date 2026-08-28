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
  assert.deepEqual(brief.overview, { totalAttempts: 2, successfulConversations: 1, noAnswer: 1, busy: 0, failed: 0, lastSuccessfulContact: 'Aug 25, 2026', openFollowUps: 0 });
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

test('meeting brief includes confirmed teacher notes for the selected student and range', () => {
  const teacherNotes = [
    { id: 'n1', student_id: 'emma', content: 'Parent requested transportation information.', source: 'typed', teacher_confirmed: true, created_at: '2026-08-24T10:00:00-07:00' },
    { id: 'n2', student_id: 'emma', content: 'Family agreed to practice reading at home.', source: 'voice', teacher_confirmed: true, created_at: '2026-08-25T15:00:00-07:00' },
    { id: 'n3', student_id: 'emma', content: 'Do not include this unconfirmed note.', source: 'voice', teacher_confirmed: false, created_at: '2026-08-25T16:00:00-07:00' },
    { id: 'n4', student_id: 'lucas', content: 'Other student note.', source: 'typed', teacher_confirmed: true, created_at: '2026-08-25T16:00:00-07:00' },
    { id: 'n5', student_id: 'emma', content: 'Older note outside the selected range.', source: 'typed', teacher_confirmed: true, created_at: '2026-07-25T16:00:00-07:00' },
  ];
  const brief = buildMeetingBrief({ events, students, followUps: [], teacherNotes, studentId: 'emma', range: { preset: 'this-month' }, now });
  assert.deepEqual(brief.teacherNotes.map(note => note.content), [teacherNotes[1].content, teacherNotes[0].content]);
  assert.match(brief.concerns.join(' '), /transportation/);
  assert.match(brief.agreements.join(' '), /practice reading/);
  assert.equal(brief.overview.totalAttempts, 2);
});

test('meeting brief detailed history exposes confirmed teacher notes separately from event notes', () => {
  const brief = buildMeetingBrief({
    events,
    students,
    followUps: [],
    teacherNotes: [{ id: 'n1', student_id: 'emma', content: 'Parent requested transportation information.', source: 'typed', teacher_confirmed: true, created_at: '2026-08-24T10:00:00-07:00' }],
    studentId: 'emma',
    range: { preset: 'this-month' },
    now,
  });
  assert.equal(brief.detailedHistory.some(item => item.teacherNote === 'Parent requested transportation information.'), true);
  assert.equal(brief.detailedHistory.some(item => item.source === 'typed'), true);
});
