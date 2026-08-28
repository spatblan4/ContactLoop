import { filterEventsByRange, rangeLabel } from './date-filters.js';
import { discussedTopicsForEvent } from './call-topics.js';
import { effectiveOpenFollowUps } from './followup-items.js';

const FINAL_RESULTS = new Set(['Connected', 'No Answer', 'Busy', 'Failed']);

function formatDate(value, options = { month: 'short', day: 'numeric', year: 'numeric' }) {
  return new Intl.DateTimeFormat('en-US', options).format(new Date(value));
}

function formatDateTime(value) {
  return formatDate(value, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function noteSections(notes) {
  const concerns = [];
  const agreements = [];
  notes.forEach(note => {
    const text = note.trim();
    if (/(asked|question|request|concern|wonder|information)/i.test(text)) concerns.push(text);
    if (/(confirmed|agreed|will |attend|scheduled|send |provide )/i.test(text)) agreements.push(text);
  });
  return {
    concerns: concerns.length ? concerns : ['No parent concerns or requests recorded.'],
    agreements: agreements.length ? agreements : ['No agreements or commitments recorded.'],
  };
}

export function buildMeetingBrief({ events = [], students = [], followUps = [], teacherNotes = [], includeNotes = true, studentId, range = { preset: 'this-month' }, now = new Date(), teacherName = 'Bella Rivera' }) {
  const student = students.find(candidate => candidate.id === studentId);
  const rangeEvents = filterEventsByRange(events, range, now)
    .filter(event => FINAL_RESULTS.has(event.result) && (!studentId || event.studentId === studentId));
  const rangeTeacherNotes = includeNotes
    ? filterEventsByRange(teacherNotes.map(note => ({ ...note, callTime: note.createdAt ?? note.created_at })), range, now)
      .filter(note => (note.studentId ?? note.student_id) === studentId && (note.teacherConfirmed ?? note.teacher_confirmed) === true)
      .sort((left, right) => new Date(right.callTime).getTime() - new Date(left.callTime).getTime())
    : [];
  const openFollowUps = effectiveOpenFollowUps({ followUps, events })
    .filter(followUp => !studentId || (followUp.studentId ?? followUp.student_id) === studentId);
  const notes = includeNotes
    ? [...rangeEvents.map(event => event.note), ...rangeTeacherNotes.map(note => note.content)].filter(Boolean)
    : [];
  const successful = rangeEvents.filter(event => event.result === 'Connected');
  const topics = [...rangeEvents.reduce((counts, event) => {
    discussedTopicsForEvent(event).forEach(topic => counts.set(topic, (counts.get(topic) ?? 0) + 1));
    return counts;
  }, new Map())].map(([label, count]) => ({ label, count })).sort((left, right) => right.count - left.count || left.label.localeCompare(right.label));
  const afternoonSuccesses = successful.filter(event => new Date(event.callTime).getHours() >= 12).length;
  const morningUnsuccessful = rangeEvents.filter(event => new Date(event.callTime).getHours() < 12 && event.result !== 'Connected').length;
  const insights = [];
  if (successful.length && afternoonSuccesses > successful.length / 2) insights.push('Most successful calls occurred in the afternoon.');
  if (morningUnsuccessful >= 3) insights.push(`${morningUnsuccessful} morning attempts were unsuccessful.`);

  return {
    student,
    teacherName,
    reportingPeriod: rangeLabel(range, now),
    generatedDate: formatDate(now),
    overview: {
      totalAttempts: rangeEvents.length,
      successfulConversations: successful.length,
      noAnswer: rangeEvents.filter(event => event.result === 'No Answer').length,
      busy: rangeEvents.filter(event => event.result === 'Busy').length,
      failed: rangeEvents.filter(event => event.result === 'Failed').length,
      lastSuccessfulContact: successful.length ? formatDate(successful.sort((left, right) => new Date(right.callTime) - new Date(left.callTime))[0].callTime) : 'None recorded',
      openFollowUps: openFollowUps.length,
    },
    topics,
    teacherNotes: rangeTeacherNotes,
    ...noteSections(notes),
    openFollowUps,
    insights,
    detailedHistory: [
      ...[...rangeEvents].sort((left, right) => new Date(right.callTime) - new Date(left.callTime)).map(event => ({
      ...event,
      topic: discussedTopicsForEvent(event).join(', ') || '—',
      displayTime: formatDateTime(event.callTime),
      followUpStatus: event.result === 'Connected' ? 'Completed' : (openFollowUps.some(followUp => followUp.id === event.followUpId || followUp.contactEventId === event.id) ? 'Open' : '—'),
      })),
      ...rangeTeacherNotes.map(note => ({
        id: `teacher-note-${note.id}`,
        kind: 'teacher-note',
        callTime: note.callTime,
        displayTime: formatDateTime(note.callTime),
        result: 'Teacher note',
        duration: null,
        topic: '—',
        note: note.content,
        teacherNote: note.content,
        source: note.source,
        followUpStatus: '—',
      })),
    ].sort((left, right) => new Date(right.callTime) - new Date(left.callTime)),
  };
}
