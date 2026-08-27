import assert from 'node:assert/strict';
import test from 'node:test';

const moduleUrl = new URL('../src/lib/student-search.js', import.meta.url);
const students = [
  { id: 'emma', name: 'Emma Johnson', parent: 'Sarah Johnson', relation: 'Mom', phone: '(415) 555-0188' },
  { id: 'lucas', name: 'Lucas Smith', parent: 'David Smith', relation: 'Dad', phone: '(415) 555-0142' },
];

test('student search matches names, guardians, and phone numbers', async () => {
  const { filterStudents = () => [] } = await import(moduleUrl).catch(() => ({}));

  assert.deepEqual(filterStudents(students, 'emma').map(student => student.id), ['emma']);
  assert.deepEqual(filterStudents(students, 'sarah').map(student => student.id), ['emma']);
  assert.deepEqual(filterStudents(students, '0142').map(student => student.id), ['lucas']);
});

test('empty search returns all students and unknown search returns none', async () => {
  const { filterStudents = () => [] } = await import(moduleUrl).catch(() => ({}));

  assert.deepEqual(filterStudents(students, '').map(student => student.id), ['emma', 'lucas']);
  assert.deepEqual(filterStudents(students, 'does-not-exist'), []);
});
