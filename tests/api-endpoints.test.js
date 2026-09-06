import test from 'node:test';
import assert from 'node:assert/strict';
import { setApiBaseUrl, ApiError } from '../src/lib/api/client.js';
import * as studentsApi from '../src/lib/api/students.js';
import * as guardiansApi from '../src/lib/api/guardians.js';
import * as contactEventsApi from '../src/lib/api/contact-events.js';
import * as followUpsApi from '../src/lib/api/follow-ups.js';
import * as teacherNotesApi from '../src/lib/api/teacher-notes.js';
import * as aiBriefsApi from '../src/lib/api/ai-briefs.js';
import { getDashboardSummary } from '../src/lib/api/data.js';
import {
  createStudent,
  deleteStudent,
  listGuardians,
  createGuardian,
  updateGuardian,
  deleteGuardian,
  updateContactEvent,
  deleteContactEvent,
  createFollowUp,
  deleteFollowUp,
  updateTeacherNote,
  deleteTeacherNote,
  saveAiContactBrief,
  updateAiContactBrief,
  approveAiContactBrief,
  supersedeAiContactBrief,
  removeAiContactBrief,
} from '../src/lib/supabase.js';

setApiBaseUrl('http://localhost:8000');

const jsonResponse = (status, payload) => ({
  ok: status >= 200 && status < 300,
  status,
  text: async () => JSON.stringify(payload),
});

const noContent = () => ({ ok: true, status: 204, text: async () => '' });

async function withMockFetch(handler, run) {
  const originalFetch = globalThis.fetch;
  const requests = [];
  globalThis.fetch = async (url, init) => {
    const request = { url: String(url), init };
    requests.push(request);
    return handler(request);
  };
  try {
    return { result: await run(), requests };
  } finally {
    globalThis.fetch = originalFetch;
  }
}

function expectRoutes(requests, expected) {
  assert.deepEqual(requests.map(request => [request.init.method, request.url]), expected);
}

test('students module maps CRUD to the right method and path', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), async () => {
    await studentsApi.listStudents({ search: 'em' });
    await studentsApi.listStudents();
    await studentsApi.getStudent('s1');
    await studentsApi.createStudent({ name: 'Emma Johnson', guardians: [] });
    await studentsApi.updateStudent('s1', { name: 'Emma J.' });
    await studentsApi.deleteStudent('s1');
  });
  expectRoutes(requests, [
    ['GET', 'http://localhost:8000/api/v1/students?search=em'],
    ['GET', 'http://localhost:8000/api/v1/students'],
    ['GET', 'http://localhost:8000/api/v1/students/s1'],
    ['POST', 'http://localhost:8000/api/v1/students'],
    ['PATCH', 'http://localhost:8000/api/v1/students/s1'],
    ['DELETE', 'http://localhost:8000/api/v1/students/s1'],
  ]);
  assert.deepEqual(JSON.parse(requests[3].init.body), { name: 'Emma Johnson', guardians: [] });
  assert.deepEqual(JSON.parse(requests[4].init.body), { name: 'Emma J.' });
});

test('guardians module maps CRUD to the right method and path', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), async () => {
    await guardiansApi.listGuardians({ student_id: 's1' });
    await guardiansApi.listGuardians();
    await guardiansApi.getGuardian('g1');
    await guardiansApi.createGuardian({ student_id: 's1', name: 'Sarah Johnson', relation: 'Mom' });
    await guardiansApi.updateGuardian('g1', { phone: '4155550000' });
    await guardiansApi.deleteGuardian('g1');
  });
  expectRoutes(requests, [
    ['GET', 'http://localhost:8000/api/v1/guardians?student_id=s1'],
    ['GET', 'http://localhost:8000/api/v1/guardians'],
    ['GET', 'http://localhost:8000/api/v1/guardians/g1'],
    ['POST', 'http://localhost:8000/api/v1/guardians'],
    ['PATCH', 'http://localhost:8000/api/v1/guardians/g1'],
    ['DELETE', 'http://localhost:8000/api/v1/guardians/g1'],
  ]);
});

test('contact-events module maps CRUD and list filters to the right method and path', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), async () => {
    await contactEventsApi.listContactEvents({ student_id: 's1', from: '2026-09-01', to: '2026-09-06', result: 'Connected' });
    await contactEventsApi.listContactEvents();
    await contactEventsApi.getContactEvent('e1');
    await contactEventsApi.createContactEvent({ student_id: 's1', guardian_id: 'g1', result: 'No Answer' });
    await contactEventsApi.updateContactEvent('e1', { result: 'Connected' });
    await contactEventsApi.deleteContactEvent('e1');
  });
  expectRoutes(requests, [
    ['GET', 'http://localhost:8000/api/v1/contact-events?student_id=s1&from=2026-09-01&to=2026-09-06&result=Connected'],
    ['GET', 'http://localhost:8000/api/v1/contact-events'],
    ['GET', 'http://localhost:8000/api/v1/contact-events/e1'],
    ['POST', 'http://localhost:8000/api/v1/contact-events'],
    ['PATCH', 'http://localhost:8000/api/v1/contact-events/e1'],
    ['DELETE', 'http://localhost:8000/api/v1/contact-events/e1'],
  ]);
});

test('follow-ups module maps CRUD to the right method and path', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), async () => {
    await followUpsApi.listFollowUps({ status: 'open', student_id: 's1' });
    await followUpsApi.getFollowUp('f1');
    await followUpsApi.createFollowUp({ student_id: 's1', due_at: '2026-09-08T09:00:00Z' });
    await followUpsApi.updateFollowUp('f1', { status: 'completed' });
    await followUpsApi.deleteFollowUp('f1');
  });
  expectRoutes(requests, [
    ['GET', 'http://localhost:8000/api/v1/follow-ups?status=open&student_id=s1'],
    ['GET', 'http://localhost:8000/api/v1/follow-ups/f1'],
    ['POST', 'http://localhost:8000/api/v1/follow-ups'],
    ['PATCH', 'http://localhost:8000/api/v1/follow-ups/f1'],
    ['DELETE', 'http://localhost:8000/api/v1/follow-ups/f1'],
  ]);
});

test('teacher-notes module maps CRUD to the right method and path', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), async () => {
    await teacherNotesApi.listTeacherNotes({ student_id: 's1' });
    await teacherNotesApi.getTeacherNote('n1');
    await teacherNotesApi.createTeacherNote({ student_id: 's1', content: 'Met the parent.' });
    await teacherNotesApi.updateTeacherNote('n1', { teacher_confirmed: true });
    await teacherNotesApi.deleteTeacherNote('n1');
  });
  expectRoutes(requests, [
    ['GET', 'http://localhost:8000/api/v1/teacher-notes?student_id=s1'],
    ['GET', 'http://localhost:8000/api/v1/teacher-notes/n1'],
    ['POST', 'http://localhost:8000/api/v1/teacher-notes'],
    ['PATCH', 'http://localhost:8000/api/v1/teacher-notes/n1'],
    ['DELETE', 'http://localhost:8000/api/v1/teacher-notes/n1'],
  ]);
});

test('ai-briefs module maps CRUD, approve, and supersede to the right method and path', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), async () => {
    await aiBriefsApi.listAiBriefs({ student_id: 's1', latest: true });
    await aiBriefsApi.getAiBrief('b1');
    await aiBriefsApi.createAiBrief({ student_id: 's1', date_from: '2026-09-01', date_to: '2026-09-06' });
    await aiBriefsApi.updateAiBrief('b1', { status: 'approved' });
    await aiBriefsApi.approveAiBrief('b1');
    await aiBriefsApi.supersedeAiBrief('b1');
    await aiBriefsApi.deleteAiBrief('b1');
  });
  expectRoutes(requests, [
    ['GET', 'http://localhost:8000/api/v1/ai-briefs?student_id=s1&latest=true'],
    ['GET', 'http://localhost:8000/api/v1/ai-briefs/b1'],
    ['POST', 'http://localhost:8000/api/v1/ai-briefs'],
    ['PATCH', 'http://localhost:8000/api/v1/ai-briefs/b1'],
    ['POST', 'http://localhost:8000/api/v1/ai-briefs/b1/approve'],
    ['POST', 'http://localhost:8000/api/v1/ai-briefs/b1/supersede'],
    ['DELETE', 'http://localhost:8000/api/v1/ai-briefs/b1'],
  ]);
});

test('dashboard summary passes date range query params', async () => {
  const { result, requests } = await withMockFetch(
    () => jsonResponse(200, { call_attempts: 3, connected: 1, unsuccessful: 2, follow_ups_due: 1 }),
    () => getDashboardSummary({ from: '2026-09-01', to: '2026-09-06' }),
  );
  expectRoutes(requests, [['GET', 'http://localhost:8000/api/v1/dashboard/summary?from=2026-09-01&to=2026-09-06']]);
  assert.deepEqual(result, { call_attempts: 3, connected: 1, unsuccessful: 2, follow_ups_due: 1 });
});

test('createStudent facade splits the name and nests guardians', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(201, { id: 's1' }), () =>
    createStudent({ name: '  Emma Marie Johnson ', guardianName: 'Sarah Johnson', relation: 'Mom', phone: '4155550188' }),
  );
  expectRoutes(requests, [['POST', 'http://localhost:8000/api/v1/students']]);
  assert.deepEqual(JSON.parse(requests[0].init.body), {
    name: 'Emma Marie Johnson',
    first_name: 'Emma Marie',
    last_name: 'Johnson',
    guardians: [{ name: 'Sarah Johnson', relation: 'Mom', phone: '4155550188' }],
  });
});

test('createStudent facade prefers supplied guardians', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(201, { id: 's1' }), () =>
    createStudent({
      name: 'Priya Patel',
      guardians: [
        { name: 'Anita Patel', relation: 'Mom', phone: '4155550111' },
        { name: 'Raj Patel', relation: 'Dad', phone: null },
      ],
    }),
  );
  assert.deepEqual(JSON.parse(requests[0].init.body), {
    name: 'Priya Patel',
    first_name: 'Priya',
    last_name: 'Patel',
    guardians: [
      { name: 'Anita Patel', relation: 'Mom', phone: '4155550111' },
      { name: 'Raj Patel', relation: 'Dad', phone: null },
    ],
  });
});

test('deleteStudent facade soft-deletes and sends no JSON body on 204', async () => {
  const { result, requests } = await withMockFetch(() => noContent(), () => deleteStudent('s1'));
  assert.equal(result ?? null, null);
  assert.equal(requests.length, 1);
  assert.equal(requests[0].init.method, 'DELETE');
  assert.equal(requests[0].url, 'http://localhost:8000/api/v1/students/s1');
  assert.equal(requests[0].init.body, undefined);
  assert.equal(requests[0].init.headers['Content-Type'], undefined);
});

test('apiFetch resolves null for 204 responses', async () => {
  const result = await studentsApi.deleteStudent('s1', { fetchImpl: () => noContent() });
  assert.equal(result, null);
});

test('guardian facade CRUD exports map to the right routes', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), async () => {
    await listGuardians({ studentId: 's1' });
    await createGuardian({ student_id: 's1', name: 'Sarah Johnson', relation: 'Mom' });
    await updateGuardian('g1', { preferred_contact_method: 'phone' });
    await deleteGuardian('g1');
  });
  expectRoutes(requests, [
    ['GET', 'http://localhost:8000/api/v1/guardians?student_id=s1'],
    ['POST', 'http://localhost:8000/api/v1/guardians'],
    ['PATCH', 'http://localhost:8000/api/v1/guardians/g1'],
    ['DELETE', 'http://localhost:8000/api/v1/guardians/g1'],
  ]);
});

test('contact-event facade update and delete map to the right routes', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), async () => {
    await updateContactEvent('e1', { result: 'Connected', ended_at: '2026-09-06T10:00:00Z' });
    await deleteContactEvent('e1');
  });
  expectRoutes(requests, [
    ['PATCH', 'http://localhost:8000/api/v1/contact-events/e1'],
    ['DELETE', 'http://localhost:8000/api/v1/contact-events/e1'],
  ]);
  assert.deepEqual(JSON.parse(requests[0].init.body), { result: 'Connected', ended_at: '2026-09-06T10:00:00Z' });
});

test('follow-up facade create and delete map to the right routes', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), async () => {
    await createFollowUp({ student_id: 's1', due_at: '2026-09-08T09:00:00Z', status: 'open' });
    await deleteFollowUp('f1');
  });
  expectRoutes(requests, [
    ['POST', 'http://localhost:8000/api/v1/follow-ups'],
    ['DELETE', 'http://localhost:8000/api/v1/follow-ups/f1'],
  ]);
  assert.deepEqual(JSON.parse(requests[0].init.body), { student_id: 's1', due_at: '2026-09-08T09:00:00Z', status: 'open' });
});

test('teacher-note facade update and delete map to the right routes', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), async () => {
    await updateTeacherNote('n1', { content: 'Updated note.' });
    await deleteTeacherNote('n1');
  });
  expectRoutes(requests, [
    ['PATCH', 'http://localhost:8000/api/v1/teacher-notes/n1'],
    ['DELETE', 'http://localhost:8000/api/v1/teacher-notes/n1'],
  ]);
});

test('saveAiContactBrief facade maps the brief payload to snake_case', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(201, { id: 'b1' }), () =>
    saveAiContactBrief({
      studentId: 's1',
      dateFrom: '2026-09-01',
      dateTo: '2026-09-06',
      brief: {
        key_topics: ['Homework'],
        parent_concerns: ['Attendance'],
        recorded_resolutions: ['Called back'],
        open_items: ['Share study plan'],
        suggested_next_step: 'Schedule a follow-up call',
      },
    }),
  );
  expectRoutes(requests, [['POST', 'http://localhost:8000/api/v1/ai-briefs']]);
  assert.deepEqual(JSON.parse(requests[0].init.body), {
    student_id: 's1',
    date_from: '2026-09-01',
    date_to: '2026-09-06',
    version: 1,
    status: 'draft',
    key_topics: ['Homework'],
    parent_concerns: ['Attendance'],
    recorded_resolutions: ['Called back'],
    open_items: ['Share study plan'],
    suggested_next_step: 'Schedule a follow-up call',
  });
});

test('updateAiContactBrief facade patches status and brief fields', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), () =>
    updateAiContactBrief('b1', { status: 'approved', brief: { key_topics: ['Homework'], suggested_next_step: 'Email the parent' } }),
  );
  expectRoutes(requests, [['PATCH', 'http://localhost:8000/api/v1/ai-briefs/b1']]);
  assert.deepEqual(JSON.parse(requests[0].init.body), {
    status: 'approved',
    key_topics: ['Homework'],
    parent_concerns: [],
    recorded_resolutions: [],
    open_items: [],
    suggested_next_step: 'Email the parent',
  });
});

test('ai-brief approve, supersede, and remove facades map to the right routes', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), async () => {
    await approveAiContactBrief('b1');
    await supersedeAiContactBrief('b1');
    await removeAiContactBrief('b1');
  });
  expectRoutes(requests, [
    ['POST', 'http://localhost:8000/api/v1/ai-briefs/b1/approve'],
    ['POST', 'http://localhost:8000/api/v1/ai-briefs/b1/supersede'],
    ['DELETE', 'http://localhost:8000/api/v1/ai-briefs/b1'],
  ]);
});

test('facade mutations surface normalized ApiErrors with status and detail', async () => {
  await assert.rejects(
    () =>
      withMockFetch(() => jsonResponse(409, { detail: 'An open follow-up already exists for this guardian.' }), () =>
        createFollowUp({ student_id: 's1', due_at: '2026-09-08T09:00:00Z' }),
      ).then(({ result }) => result),
    error => {
      assert.ok(error instanceof ApiError);
      assert.equal(error.status, 409);
      assert.equal(error.message, 'An open follow-up already exists for this guardian.');
      return true;
    },
  );
  await assert.rejects(
    () =>
      withMockFetch(() => jsonResponse(404, { detail: 'Student not found.' }), () => deleteStudent('missing')).then(
        ({ result }) => result,
      ),
    error => {
      assert.ok(error instanceof ApiError);
      assert.equal(error.status, 404);
      return true;
    },
  );
});
