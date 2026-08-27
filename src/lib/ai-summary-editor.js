const LIST_FIELDS = ['key_topics', 'parent_concerns', 'recorded_resolutions', 'open_items'];

function cloneBrief(brief = {}) {
  return {
    key_topics: [...(brief.key_topics ?? [])],
    parent_concerns: [...(brief.parent_concerns ?? [])],
    recorded_resolutions: [...(brief.recorded_resolutions ?? [])],
    open_items: [...(brief.open_items ?? [])],
    suggested_next_step: brief.suggested_next_step ?? '',
  };
}

export function createEditableBrief(brief) {
  const snapshot = cloneBrief(brief);
  return { brief: cloneBrief(snapshot), original: snapshot };
}

export function updateBriefItem(editor, field, index, value) {
  if (!LIST_FIELDS.includes(field)) return editor;
  const brief = cloneBrief(editor.brief);
  if (index >= 0 && index < brief[field].length && String(value).trim()) brief[field][index] = String(value).trim();
  return { ...editor, brief };
}

export function addBriefItem(editor, field, value) {
  if (!LIST_FIELDS.includes(field) || !String(value).trim()) return editor;
  const brief = cloneBrief(editor.brief);
  brief[field].push(String(value).trim());
  return { ...editor, brief };
}

export function deleteBriefItem(editor, field, index) {
  if (!LIST_FIELDS.includes(field)) return editor;
  const brief = cloneBrief(editor.brief);
  if (index >= 0 && index < brief[field].length) brief[field].splice(index, 1);
  return { ...editor, brief };
}

export function cancelBriefEdits(editor) {
  return { ...editor, brief: cloneBrief(editor.original) };
}

export function buildDraftVersion(previous, brief) {
  return {
    previous: previous?.id ? { id: previous.id, status: 'superseded' } : null,
    next: { version: (previous?.version ?? 0) + 1, status: 'draft', brief: cloneBrief(brief) },
  };
}

export function approvedBriefStatus() {
  return 'approved';
}

export { cloneBrief };
