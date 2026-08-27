import test from 'node:test';
import assert from 'node:assert/strict';
import { importStudents } from '../src/lib/supabase.js';

test('importStudents calls the owner-derived RPC without teacher_id', async () => {
  let request;
  const client = {
    rpc: async (name, body) => { request = { name, body }; return { data: { students_imported: 1, guardians_imported: 2 }, error: null }; },
  };
  const result = await importStudents({
    students: [{ student_key: 'emma-johnson', name: 'Emma Johnson', first_name: 'Emma', last_name: 'Johnson' }],
    guardians: [
      { student_key: 'emma-johnson', name: 'Sarah Johnson', relationship: 'Mom', phone: '4155550188', email: 'sarah@example.com' },
      { student_key: 'emma-johnson', name: 'David Johnson', relationship: 'Dad', phone: '4155550142', email: '' },
    ],
  }, client);
  assert.deepEqual(result, { students_imported: 1, guardians_imported: 2 });
  assert.equal(request.name, 'import_students');
  assert.deepEqual(request.body, {
    p_students: [{ student_key: 'emma-johnson', name: 'Emma Johnson', first_name: 'Emma', last_name: 'Johnson' }],
    p_guardians: [
      { student_key: 'emma-johnson', name: 'Sarah Johnson', relationship: 'Mom', phone: '4155550188', email: 'sarah@example.com' },
      { student_key: 'emma-johnson', name: 'David Johnson', relationship: 'Dad', phone: '4155550142', email: '' },
    ],
  });
  assert.equal('teacher_id' in request.body, false);
});

test('importStudents surfaces the database error', async () => {
  const client = { rpc: async () => ({ data: null, error: { message: 'Authentication is required.' } }) };
  await assert.rejects(() => importStudents({ students: [], guardians: [] }, client), /Authentication is required/);
});
