import test from 'node:test';
import assert from 'node:assert/strict';
import { importStudents } from '../src/lib/supabase.js';
import { setApiBaseUrl } from '../src/lib/api/client.js';

setApiBaseUrl('http://localhost:8000');

const jsonResponse = (status, payload) => ({
  ok: status >= 200 && status < 300,
  status,
  text: async () => JSON.stringify(payload),
});

test('importStudents posts the roster to the import endpoint and maps the result', async () => {
  let request;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    request = { url: String(url), init };
    return jsonResponse(200, { imported_students: 1, imported_guardians: 2 });
  };
  try {
    const result = await importStudents({
      students: [{ student_key: 'emma-johnson', name: 'Emma Johnson', first_name: 'Emma', last_name: 'Johnson' }],
      guardians: [
        { student_key: 'emma-johnson', name: 'Sarah Johnson', relationship: 'Mom', phone: '4155550188', email: 'sarah@example.com' },
        { student_key: 'emma-johnson', name: 'David Johnson', relationship: 'Dad', phone: '4155550142', email: '' },
      ],
    });
    assert.deepEqual(result, { students_imported: 1, guardians_imported: 2 });
    assert.equal(request.url, 'http://localhost:8000/api/v1/import/students');
    assert.equal(request.init.method, 'POST');
    assert.deepEqual(JSON.parse(request.init.body), {
      students: [{ student_key: 'emma-johnson', name: 'Emma Johnson', first_name: 'Emma', last_name: 'Johnson' }],
      guardians: [
        { student_key: 'emma-johnson', name: 'Sarah Johnson', relationship: 'Mom', phone: '4155550188', email: 'sarah@example.com' },
        { student_key: 'emma-johnson', name: 'David Johnson', relationship: 'Dad', phone: '4155550142', email: '' },
      ],
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('importStudents surfaces the server error detail', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => jsonResponse(401, { detail: 'Authentication is required.' });
  try {
    await assert.rejects(() => importStudents({ students: [], guardians: [] }), /Authentication is required/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
