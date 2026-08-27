import { filterEventsByRange } from './date-filters.js';
import { discussedTopicsForEvent, topicLabel } from './call-topics.js';

function searchableText(event, student) {
  return [student?.name, student?.parent, student?.relation, event.result, event.plannedTopic, event.planned_topic, topicLabel(event.plannedTopic ?? event.planned_topic, event.discussedTopics ?? event.discussed_topics ?? [], event.result), event.note].filter(Boolean).join(' ').toLowerCase();
}

export function filterContactLogEvents(events, filters = {}, students = [], now = new Date()) {
  const studentById = new Map(students.map(student => [student.id, student]));
  const search = String(filters.search ?? '').trim().toLowerCase();
  const ranged = filterEventsByRange(events, filters.range ?? { preset: 'this-month' }, now);
  return ranged.filter(event => {
    const student = studentById.get(event.studentId ?? event.student_id);
    const matchesSearch = !search || searchableText(event, student).includes(search);
    const matchesOutcome = !filters.outcome || filters.outcome === 'all' || event.result === filters.outcome;
    const matchesStudent = !filters.studentId || filters.studentId === 'all' || (event.studentId ?? event.student_id) === filters.studentId;
    return matchesSearch && matchesOutcome && matchesStudent;
  });
}

function csvCell(value) {
  const text = String(value ?? '—');
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function toContactLogCsv(events, students = []) {
  const studentById = new Map(students.map(student => [student.id, student]));
  const header = ['Student', 'Parent', 'When', 'Outcome', 'Duration', 'Planned Topic', 'Discussed Topics', 'Attempt'];
  const rows = events.map(event => {
    const student = studentById.get(event.studentId ?? event.student_id) ?? {};
    const planned = event.plannedTopic ?? event.planned_topic ?? null;
    return [student.name, student.parent, event.callTime ?? event.call_time, event.result, event.duration, planned, discussedTopicsForEvent(event).join(', ') || null, event.attemptNumber].map(csvCell);
  });
  return [header.join(','), ...rows.map(row => row.join(','))].join('\n');
}
