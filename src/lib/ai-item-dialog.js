const ITEM_LABELS = {
  key_topics: 'Key topic',
  parent_concerns: 'Parent concern',
  recorded_resolutions: 'Recorded resolution',
  open_items: 'Open item',
};

export function aiItemLabel(field) {
  return ITEM_LABELS[field] || 'Summary item';
}

export function createAiItemDialogState(field) {
  return { step: 'ai-add-item', field, value: '', error: null };
}
