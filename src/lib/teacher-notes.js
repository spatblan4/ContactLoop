export function notesForStudent(notes = [], studentId) {
  return notes
    .filter(note => note.student_id === studentId || note.studentId === studentId)
    .sort((a, b) => new Date(b.created_at || b.createdAt).getTime() - new Date(a.created_at || a.createdAt).getTime());
}

export function teacherNoteSourceLabel(source) {
  if (source === 'voice') return 'Voice note';
  if (source === 'ai') return 'AI draft · needs review';
  return 'Typed note';
}

export function normalizeTeacherNote(note) {
  return {
    id: note.id,
    studentId: note.student_id,
    content: note.content,
    source: note.source,
    teacherConfirmed: note.teacher_confirmed,
    createdAt: note.created_at,
  };
}
