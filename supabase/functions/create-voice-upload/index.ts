import { corsHeadersFor, createUploadUrl, json } from '../_shared/voice.ts';

Deno.serve(async request => {
  if (request.method === 'OPTIONS') return new Response('ok', { headers: corsHeadersFor(request) });
  try {
    const body = await request.json();
    const studentId = String(body.student_id || '');
    const contentType = String(body.content_type || 'audio/webm');
    if (!/^[0-9a-f-]{36}$/i.test(studentId)) return json({ error: 'Invalid student.' }, 400, request);
    if (!contentType.startsWith('audio/')) return json({ error: 'Invalid audio type.' }, 400, request);
    return json(await createUploadUrl(`voice-notes/${studentId}/${crypto.randomUUID()}.webm`, contentType), 200, request);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to create upload.';
    console.error('create-voice-upload failed:', message);
    return json({ error: `Upload setup failed: ${message}` }, 502, request);
  }
});
