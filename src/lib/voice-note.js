export function createVoiceNoteState() {
  return { status: 'idle', elapsedSeconds: 0, transcript: '', error: null };
}

export function canSaveVoiceNote(state) {
  return state?.status === 'review' && Boolean(state.transcript?.trim());
}

export function voiceNoteError(message) {
  return { ...createVoiceNoteState(), status: 'error', error: message };
}
