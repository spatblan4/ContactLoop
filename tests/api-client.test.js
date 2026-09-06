import test from 'node:test';
import assert from 'node:assert/strict';
import { apiFetch, setApiBaseUrl, hasBackendConfig, ApiError } from '../src/lib/api/client.js';
import {
  createContactEvent,
  createTeacherNote,
  createVoiceUpload,
  getVoiceTranscriptStatus,
  invokeContactBrief,
  listFollowUps,
  loadContactLoopData,
  startVoiceTranscription,
  updateStudent,
} from '../src/lib/supabase.js';

setApiBaseUrl('http://localhost:8000');
assert.equal(hasBackendConfig(), true);

const jsonResponse = (status, payload) => ({
  ok: status >= 200 && status < 300,
  status,
  text: async () => JSON.stringify(payload),
});

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

test('apiFetch normalizes server detail errors', async () => {
  await assert.rejects(
    () => apiFetch('/api/v1/students', { fetchImpl: async () => jsonResponse(404, { detail: 'Student not found.' }) }),
    error => {
      assert.ok(error instanceof ApiError);
      assert.equal(error.message, 'Student not found.');
      assert.equal(error.detail, 'Student not found.');
      assert.equal(error.status, 404);
      return true;
    },
  );
});

test('apiFetch normalizes FastAPI validation errors', async () => {
  await assert.rejects(
    () => apiFetch('/api/v1/students', {
      method: 'POST',
      body: {},
      fetchImpl: async () => jsonResponse(400, { detail: [{ loc: ['body', 'name'], msg: 'Field required' }] }),
    }),
    /name: Field required/,
  );
});

test('apiFetch falls back to a status message when the body is empty', async () => {
  await assert.rejects(
    () => apiFetch('/api/v1/students', { fetchImpl: async () => ({ ok: false, status: 500, text: async () => '' }) }),
    /status 500/,
  );
});

test('apiFetch requires a configured base URL', async () => {
  setApiBaseUrl('');
  try {
    await assert.rejects(() => apiFetch('/api/v1/students', { fetchImpl: async () => jsonResponse(200, {}) }), /VITE_API_BASE_URL/);
    assert.equal(hasBackendConfig(), false);
  } finally {
    setApiBaseUrl('http://localhost:8000');
  }
});

test('loadContactLoopData maps the aggregate payload to the UI shape', async () => {
  const aggregate = {
    students: [{ id: 's1', name: 'Emma Johnson', initials: 'EJ', accent: 'sage', guardians: [{ id: 'g1', name: 'Sarah Johnson', relation: 'Mom', phone: '4155550188' }] }],
    events: [{ id: 'e1', student_id: 's1', guardian_id: 'g1', result: 'Connected', attempt_number: 1, discussed_topics: [] }],
    follow_ups: [{ id: 'f1', student_id: 's1', guardian_id: 'g1', due_at: '2026-09-08T09:00:00Z', status: 'open' }],
    teacher_notes: [{ id: 'n1', student_id: 's1', content: 'Met the parent.', source: 'typed', teacher_confirmed: true, created_at: '2026-09-06T10:00:00Z' }],
    ai_briefs: [{ id: 'b1', student_id: 's1', version: 1, status: 'draft', key_topics: [] }],
  };
  const { result } = await withMockFetch(() => jsonResponse(200, aggregate), () => loadContactLoopData());
  assert.deepEqual(result, {
    students: aggregate.students,
    events: aggregate.events,
    followUps: aggregate.follow_ups,
    teacherNotes: aggregate.teacher_notes,
    aiBriefs: aggregate.ai_briefs,
    setupRequired: false,
  });
});

test('loadContactLoopData reports setupRequired when the backend is not configured', async () => {
  setApiBaseUrl('');
  try {
    const result = await loadContactLoopData();
    assert.deepEqual(result, { students: [], events: [], followUps: [], teacherNotes: [], aiBriefs: [], setupRequired: true });
  } finally {
    setApiBaseUrl('http://localhost:8000');
  }
});

test('createContactEvent posts the normalized payload', async () => {
  const { result, requests } = await withMockFetch(
    () => jsonResponse(201, { id: 'e1', student_id: 's1', attempt_number: 2 }),
    () => createContactEvent({
      studentId: 's1',
      guardianId: 'g1',
      result: 'No Answer',
      durationSeconds: null,
      plannedTopic: 'IEP progress',
      discussedTopics: [],
      topic: null,
      teacherNote: 'Left a voicemail',
      followUpDueAt: '2026-09-08T09:00:00.000Z',
    }),
  );
  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, 'http://localhost:8000/api/v1/contact-events');
  assert.equal(requests[0].init.method, 'POST');
  assert.deepEqual(JSON.parse(requests[0].init.body), {
    student_id: 's1',
    guardian_id: 'g1',
    result: 'No Answer',
    duration_seconds: null,
    planned_topic: 'IEP progress',
    discussed_topics: [],
    topic: null,
    teacher_note: 'Left a voicemail',
    follow_up_due_at: '2026-09-08T09:00:00.000Z',
  });
  assert.deepEqual(result, { id: 'e1', student_id: 's1', attempt_number: 2 });
});

test('updateStudent patches the student and the guardian', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, {}), () =>
    updateStudent({ studentId: 's1', guardianId: 'g1', name: 'Emma J.', guardianName: 'Sarah J.', relation: 'Mom', phone: '4155550000' }),
  );
  assert.deepEqual(requests.map(request => [request.url, request.init.method]), [
    ['http://localhost:8000/api/v1/students/s1', 'PATCH'],
    ['http://localhost:8000/api/v1/guardians/g1', 'PATCH'],
  ]);
  assert.deepEqual(JSON.parse(requests[0].init.body), { name: 'Emma J.' });
  assert.deepEqual(JSON.parse(requests[1].init.body), { name: 'Sarah J.', relation: 'Mom', phone: '4155550000' });
  await assert.rejects(() => updateStudent({ studentId: '', guardianId: 'g1', name: 'x', guardianName: 'y', relation: 'Mom', phone: 'z' }), /required/i);
});

test('createTeacherNote validates content and posts snake_case fields', async () => {
  await assert.rejects(() => createTeacherNote({ studentId: 's1', content: '   ' }), /confirmed note is required/i);
  const { requests } = await withMockFetch(() => jsonResponse(201, { id: 'n1' }), () =>
    createTeacherNote({ studentId: 's1', content: ' Parent asked about homework. ', source: 'typed' }),
  );
  assert.equal(requests[0].url, 'http://localhost:8000/api/v1/teacher-notes');
  assert.deepEqual(JSON.parse(requests[0].init.body), { student_id: 's1', content: 'Parent asked about homework.', source: 'typed' });
});

test('voice helpers map snake_case responses to the UI shape', async () => {
  const { result } = await withMockFetch(
    () => jsonResponse(201, { upload_url: 'http://localhost:8000/api/v1/voice/files/abc', object_key: 'abc' }),
    () => createVoiceUpload({ studentId: 's1', contentType: 'audio/webm' }),
  );
  assert.deepEqual(result, { uploadUrl: 'http://localhost:8000/api/v1/voice/files/abc', objectKey: 'abc' });

  const { result: job } = await withMockFetch(
    () => jsonResponse(201, { job_id: 'job-9' }),
    () => startVoiceTranscription({ studentId: 's1', objectKey: 'abc' }),
  );
  assert.deepEqual(job, { jobId: 'job-9' });

  const { result: status, requests } = await withMockFetch(
    () => jsonResponse(200, { status: 'completed', transcript: 'Voice note saved locally.' }),
    () => getVoiceTranscriptStatus({ studentId: 's1', jobId: 'job-9', objectKey: 'abc' }),
  );
  assert.deepEqual(status, { status: 'completed', transcript: 'Voice note saved locally.' });
  assert.equal(requests[0].url, 'http://localhost:8000/api/v1/voice/transcriptions/job-9');
});

test('invokeContactBrief posts to the AI contact brief endpoint', async () => {
  const { result, requests } = await withMockFetch(
    () => jsonResponse(200, { brief: { key_topics: ['Homework'] } }),
    () => invokeContactBrief({ student_id: 's1', date_from: '2026-09-01', date_to: '2026-09-06', include_notes: true }),
  );
  assert.equal(requests[0].url, 'http://localhost:8000/api/v1/ai/contact-brief/generate');
  assert.equal(requests[0].init.method, 'POST');
  assert.deepEqual(result, { brief: { key_topics: ['Homework'] } });
});

test('listFollowUps passes status and student query params', async () => {
  const { requests } = await withMockFetch(() => jsonResponse(200, []), () => listFollowUps({ status: 'open', studentId: 's1' }));
  assert.equal(requests[0].url, 'http://localhost:8000/api/v1/follow-ups?status=open&student_id=s1');
});
