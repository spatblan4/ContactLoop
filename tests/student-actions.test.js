import test from 'node:test';
import assert from 'node:assert/strict';
import { studentDeletionOrder, studentDeletionRequests } from '../src/lib/student-actions.js';

test('student deletion removes dependent records before guardians and students', () => {
  const order = studentDeletionOrder();

  assert.deepEqual(order, [
    'teacher_notes',
    'ai_contact_briefs',
    'follow_ups',
    'contact_events',
    'guardians',
    'students',
  ]);
  assert.ok(order.indexOf('contact_events') < order.indexOf('guardians'));
  assert.ok(order.indexOf('guardians') < order.indexOf('students'));
});

test('student deletion targets each table by the correct key', () => {
  assert.deepEqual(studentDeletionRequests('student-123'), [
    { table: 'teacher_notes', column: 'student_id', value: 'student-123' },
    { table: 'ai_contact_briefs', column: 'student_id', value: 'student-123' },
    { table: 'follow_ups', column: 'student_id', value: 'student-123' },
    { table: 'contact_events', column: 'student_id', value: 'student-123' },
    { table: 'guardians', column: 'student_id', value: 'student-123' },
    { table: 'students', column: 'id', value: 'student-123' },
  ]);
});
