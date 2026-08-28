import test from 'node:test';
import assert from 'node:assert/strict';
import {
  createEditableBrief,
  updateBriefItem,
  addBriefItem,
  deleteBriefItem,
  cancelBriefEdits,
  buildDraftVersion,
  approvedBriefStatus,
  summaryEditPlan,
} from '../src/lib/ai-summary-editor.js';

const brief = {
  key_topics: ['Learning progress'],
  parent_concerns: [],
  recorded_resolutions: ['Reading support discussed'],
  open_items: [],
  suggested_next_step: 'Call parent next week',
};

test('summary editor can add, edit, and delete narrative items', () => {
  let edited = createEditableBrief(brief);
  edited = addBriefItem(edited, 'parent_concerns', 'Homework is difficult at home.');
  edited = updateBriefItem(edited, 'key_topics', 0, 'Academic progress');
  edited = deleteBriefItem(edited, 'recorded_resolutions', 0);

  assert.deepEqual(edited.brief, {
    key_topics: ['Academic progress'],
    parent_concerns: ['Homework is difficult at home.'],
    recorded_resolutions: [],
    open_items: [],
    suggested_next_step: 'Call parent next week',
  });
});

test('cancel restores the brief snapshot from before editing', () => {
  const original = createEditableBrief(brief);
  const edited = addBriefItem(original, 'open_items', 'Send reading resources.');
  assert.deepEqual(cancelBriefEdits(edited).brief, original.brief);
});

test('new generated version is draft and prior approved version is superseded', () => {
  assert.equal(approvedBriefStatus(), 'approved');
  assert.deepEqual(buildDraftVersion({ id: 'v1', version: 1, status: 'approved' }, brief), {
    previous: { id: 'v1', status: 'superseded' },
    next: { version: 2, status: 'draft', brief },
  });
});

test('editing an approved summary creates a new draft version', () => {
  assert.deepEqual(summaryEditPlan({ id: 'v1', version: 1, status: 'approved' }), {
    mode: 'new-version',
    previousId: 'v1',
    version: 2,
  });
  assert.deepEqual(summaryEditPlan({ id: 'v2', version: 2, status: 'draft' }), {
    mode: 'update',
    id: 'v2',
    version: 2,
  });
});
