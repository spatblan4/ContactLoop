import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildMeetingBrief } from '../src/lib/meeting-brief.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const styles = fs.readFileSync(path.join(here, '../src/styles.css'), 'utf8');

const now = new Date(2026, 7, 25, 12);
const localISO = (month, day, hour, minute = 0) => new Date(2026, month - 1, day, hour, minute).toISOString();
const students = [{ id: 'emma', name: 'Emma Johnson', relation: 'Mom', parent: 'Sarah Johnson' }];
const events = [
  { id: '1', studentId: 'emma', result: 'No Answer', callTime: localISO(8, 22, 10, 0), duration: null, topic: null, note: null, followUpId: 'f1' },
  { id: '2', studentId: 'emma', result: 'Connected', callTime: localISO(8, 25, 14, 0), duration: '7m 43s', topic: 'IEP', note: 'Parent confirmed Friday meeting and asked for transportation information.', followUpId: null },
];

test('meeting brief computes overview from real events and topics', () => {
  const brief = buildMeetingBrief({ events, students, followUps: [{ id: 'f1', student_id: 'emma', due_at: localISO(8, 27, 9, 0), status: 'open' }], studentId: 'emma', range: { preset: 'this-month' }, now });
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
    { id: 'n1', student_id: 'emma', content: 'Parent requested transportation information.', source: 'typed', teacher_confirmed: true, created_at: localISO(8, 24, 10, 0) },
    { id: 'n2', student_id: 'emma', content: 'Family agreed to practice reading at home.', source: 'voice', teacher_confirmed: true, created_at: localISO(8, 25, 15, 0) },
    { id: 'n3', student_id: 'emma', content: 'Do not include this unconfirmed note.', source: 'voice', teacher_confirmed: false, created_at: localISO(8, 25, 16, 0) },
    { id: 'n4', student_id: 'lucas', content: 'Other student note.', source: 'typed', teacher_confirmed: true, created_at: localISO(8, 25, 16, 0) },
    { id: 'n5', student_id: 'emma', content: 'Older note outside the selected range.', source: 'typed', teacher_confirmed: true, created_at: localISO(7, 25, 16, 0) },
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
    teacherNotes: [{ id: 'n1', student_id: 'emma', content: 'Parent requested transportation information.', source: 'typed', teacher_confirmed: true, created_at: localISO(8, 24, 10, 0) }],
    studentId: 'emma',
    range: { preset: 'this-month' },
    now,
  });
  assert.equal(brief.detailedHistory.some(item => item.teacherNote === 'Parent requested transportation information.'), true);
  assert.equal(brief.detailedHistory.some(item => item.source === 'typed'), true);
});

test('print styles keep meeting brief in a full-width desktop layout', () => {
  const printBlock = styles.slice(styles.lastIndexOf('@page'));

  assert.match(printBlock, /\.app-shell\s*\{[^}]*grid-template-columns:\s*1fr/s);
  assert.match(printBlock, /\.main\s*\{[^}]*width:\s*100%/s);
  assert.match(printBlock, /\.brief-info-grid\s*\{[^}]*grid-template-columns:\s*repeat\(4,1fr\)/s);
  assert.match(printBlock, /\.overview-grid\s*\{[^}]*grid-template-columns:\s*repeat\(6,1fr\)/s);
  assert.match(printBlock, /\.brief-columns\s*\{[^}]*grid-template-columns:\s*1fr\s+1fr/s);
  assert.match(printBlock, /@page\s*\{[^}]*margin:/s);
});
