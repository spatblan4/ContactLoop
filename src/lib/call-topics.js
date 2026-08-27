export const CALL_TOPICS = ['Behavior', 'Homework', 'Progress', 'IEP', 'Attendance', 'Scheduling', 'Other'];

export function normalizeDiscussedTopics(result, plannedTopic, discussedTopics = []) {
  if (result !== 'Connected') return [];
  const values = discussedTopics.length ? discussedTopics : (plannedTopic ? [plannedTopic] : []);
  return [...new Set(values.filter(Boolean))];
}

export function topicLabel(plannedTopic, discussedTopics = [], result) {
  if (result === 'Connected') return discussedTopics.length ? discussedTopics.join(', ') : '—';
  return plannedTopic || '—';
}

export function discussedTopicsForEvent(event) {
  if (event?.result !== 'Connected') return [];
  if (Array.isArray(event.discussedTopics) && event.discussedTopics.length) return event.discussedTopics;
  if (Array.isArray(event.discussed_topics) && event.discussed_topics.length) return event.discussed_topics;
  return event.topic ? [event.topic] : [];
}
