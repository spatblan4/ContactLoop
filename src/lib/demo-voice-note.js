export const DEMO_VOICE_TRANSCRIPT = 'Demo voice note: Parent shared an update about today\'s learning progress.';

export function createDemoVoiceNote(transcript = DEMO_VOICE_TRANSCRIPT) {
  return { status: 'review', source: 'voice', transcript };
}

export function addDemoTeacherNote(notes, studentId, content, createdAt = new Date().toISOString()) {
  return [{ id: `demo-note-${Date.now()}`, studentId, content, source: 'voice', teacherConfirmed: true, createdAt }, ...(notes || [])];
}
