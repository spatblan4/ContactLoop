import test from 'node:test';
import assert from 'node:assert/strict';
import { filterStudentsByStatus, studentStatus } from '../src/lib/student-status.js';

const students = [
  { id: 'emma' },
  { id: 'lucas' },
  { id: 'ava' },
  { id: 'noah' },
];
const events = [
  { studentId: 'emma', callTime: '2026-08-28T10:00:00Z', result: 'Connected' },
  { studentId: 'lucas', callTime: '2026-08-28T10:00:00Z', result: 'No Answer' },
  { studentId: 'ava', callTime: '2026-08-28T10:00:00Z', result: 'Connected' },
];
const followUps = [{ studentId: 'ava', status: 'open' }];

test('student status is derived from contact history and open follow-ups', () => {
  assert.equal(studentStatus('emma', { events, followUps }), 'on-track');
  assert.equal(studentStatus('lucas', { events, followUps }), 'needs-follow-up');
  assert.equal(studentStatus('ava', { events, followUps }), 'needs-follow-up');
  assert.equal(studentStatus('noah', { events, followUps }), 'not-contacted');
});

test('student status filter returns only matching students', () => {
  assert.deepEqual(filterStudentsByStatus(students, 'needs-follow-up', { events, followUps }).map(student => student.id), ['lucas', 'ava']);
  assert.deepEqual(filterStudentsByStatus(students, 'on-track', { events, followUps }).map(student => student.id), ['emma']);
  assert.deepEqual(filterStudentsByStatus(students, 'not-contacted', { events, followUps }).map(student => student.id), ['noah']);
  assert.deepEqual(filterStudentsByStatus(students, 'all', { events, followUps }).map(student => student.id), ['emma', 'lucas', 'ava', 'noah']);
});
