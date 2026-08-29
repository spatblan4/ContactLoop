import test from 'node:test';
import assert from 'node:assert/strict';
import { studentDeletionOrder, studentDeletionRequests, studentUpdateRequests } from '../src/lib/student-actions.js';

test('student edit builds updates for the student and primary guardian', () => {
  assert.deepEqual(studentUpdateRequests({
    studentId: 'student-123',
    guardianId: 'guardian-456',
    name: 'Jordan Lee',
    guardianName: 'Taylor Lee',
    relation: 'Mom',
    phone: '(415) 555-0199',
  }), [
    { table: 'students', column: 'id', value: 'student-123', updates: { name: 'Jordan Lee' } },
    { table: 'guardians', column: 'id', value: 'guardian-456', updates: { name: 'Taylor Lee', relation: 'Mom', phone: '(415) 555-0199' } },
  ]);
});

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
