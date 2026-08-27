import { corsHeadersFor, json, transcriptStatus } from '../_shared/voice.ts';
import { googleOperationPath } from '../_shared/google-operation.ts';

Deno.serve(async request => {
  if (request.method === 'OPTIONS') return new Response('ok', { headers: corsHeadersFor(request) });
  try {
    const body = await request.json();
    const studentId = String(body.student_id || '');
    const jobId = String(body.job_id || '');
    const objectKey = String(body.object_key || '');
    try {
      googleOperationPath(jobId);
    } catch {
      return json({ error: 'Invalid transcription job.' }, 400, request);
    }
    if (!/^[0-9a-f-]{36}$/i.test(studentId) || !objectKey.startsWith(`voice-notes/${studentId}/`)) return json({ error: 'Invalid transcription job.' }, 400, request);
    return json(await transcriptStatus(jobId, objectKey), 200, request);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to read transcription.';
    console.error('get-transcript-status failed:', message);
    return json({ error: `Transcript status failed: ${message}` }, 502, request);
  }
});
