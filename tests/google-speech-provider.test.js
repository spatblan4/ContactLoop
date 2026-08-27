import test from 'node:test';
import assert from 'node:assert/strict';
import { buildGcsResumableUploadRequest, buildSpeechRecognitionRequest } from '../src/lib/google-speech-provider.js';

test('builds a resumable GCS upload request for the recorded audio', () => {
  const request = buildGcsResumableUploadRequest({
    bucket: 'contactloop-voice-notes',
    objectKey: 'voice-notes/student-1/note.webm',
    contentType: 'audio/webm;codecs=opus',
  });

  assert.equal(request.url, 'https://storage.googleapis.com/upload/storage/v1/b/contactloop-voice-notes/o?uploadType=resumable&name=voice-notes%2Fstudent-1%2Fnote.webm');
  assert.deepEqual(request.headers, { 'Content-Type': 'application/json', 'X-Upload-Content-Type': 'audio/webm;codecs=opus' });
  assert.deepEqual(request.body, {});
});

test('builds a V1 long-running recognition request from a GCS object', () => {
  const request = buildSpeechRecognitionRequest({
    gcsUri: 'gs://contactloop-voice-notes/voice-notes/student-1/note.webm',
  });

  assert.deepEqual(request, {
    config: { encoding: 'WEBM_OPUS', languageCode: 'en-US', model: 'latest_long' },
    audio: { uri: 'gs://contactloop-voice-notes/voice-notes/student-1/note.webm' },
  });
});
