import { corsHeadersFor, json, startJob } from '../_shared/voice.ts';

Deno.serve(async request => {
  if (request.method === 'OPTIONS') return new Response('ok', { headers: corsHeadersFor(request) });
  try {
    const body = await request.json();
    const studentId = String(body.student_id || '');
    const objectKey = String(body.object_key || '');
    if (!/^[0-9a-f-]{36}$/i.test(studentId) || !objectKey.startsWith(`voice-notes/${studentId}/`)) return json({ error: 'Invalid voice note.' }, 400, request);
    return json({ jobId: await startJob(objectKey, studentId) }, 200, request);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to start transcription.';
    console.error('transcribe-voice-note failed:', message);
    return json({ error: `Transcription start failed: ${message}` }, 502, request);
  }
});
