import { apiFetch, API_PREFIX } from './client.js';

export function createVoiceUpload({ student_id, content_type }, options) {
  return apiFetch(`${API_PREFIX}/voice/uploads`, { method: 'POST', body: { student_id, content_type }, ...options });
}

export function startVoiceTranscription({ student_id, object_key }, options) {
  return apiFetch(`${API_PREFIX}/voice/transcriptions`, { method: 'POST', body: { student_id, object_key }, ...options });
}

export function getVoiceTranscription(jobId, options) {
  return apiFetch(`${API_PREFIX}/voice/transcriptions/${jobId}`, options);
}
