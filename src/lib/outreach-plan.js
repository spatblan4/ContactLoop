const PRIORITIES = new Set(['high', 'medium', 'low']);
const SOURCES = new Set(['agent', 'demo']);

function requiredText(value, field) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new TypeError(`Outreach plan ${field} is required.`);
  }
  return value.trim();
}

function normalizeItem(item) {
  if (!item || typeof item !== 'object' || Array.isArray(item)) {
    throw new TypeError('Outreach plan item must be an object.');
  }
  const priority = requiredText(item.priority, 'item priority').toLowerCase();
  if (!PRIORITIES.has(priority)) {
    throw new TypeError('Outreach plan item priority must be high, medium, or low.');
  }
  return {
    studentId: requiredText(item.student_id ?? item.studentId, 'item student id'),
    priority,
    reason: requiredText(item.reason, 'item reason'),
    suggestedNextStep: requiredText(item.suggested_next_step ?? item.suggestedNextStep, 'item suggested next step'),
  };
}

export function normalizeOutreachPlan(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new TypeError('Outreach plan response must be an object.');
  }
  if (!Array.isArray(payload.items)) {
    throw new TypeError('Outreach plan items must be an array.');
  }
  const source = payload.source ?? 'demo';
  if (!SOURCES.has(source)) {
    throw new TypeError('Outreach plan source must be agent or demo.');
  }
  const generatedAt = payload.generated_at ?? payload.generatedAt ?? null;
  if (generatedAt !== null && (typeof generatedAt !== 'string' || !generatedAt.trim())) {
    throw new TypeError('Outreach plan generated time must be a string.');
  }
  return { generatedAt, source, items: payload.items.map(normalizeItem) };
}
