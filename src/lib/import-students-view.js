const targetFields = [
  ['student_first_name', 'Student First Name'],
  ['student_last_name', 'Student Last Name'],
  ['student_full_name', 'Student Full Name'],
  ['guardian_name', 'Guardian Name'],
  ['relationship', 'Relationship'],
  ['phone', 'Phone'],
  ['email', 'Email'],
];

const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
const stepLabels = ['Upload', 'Match Columns', 'Review', 'Complete'];

function renderSteps(activeStep) {
  const activeIndex = ['upload', 'mapping', 'review', 'complete'].indexOf(activeStep);
  return `<div class="import-steps">${stepLabels.map((label, index) => `<div class="import-step ${index <= activeIndex ? 'active' : ''}"><span>${String(index + 1).padStart(2, '0')}</span><strong>${label}</strong></div>`).join('')}</div>`;
}

function renderHeader(state) {
  return `<div class="import-header"><div><button class="back" data-import-back>← Back to Students</button><p class="eyebrow">Roster management</p><h1>Import students</h1></div>${renderSteps(state.step)}</div>`;
}

export function renderImportUpload(state) {
  return `${renderHeader(state)}<section class="import-panel import-upload-panel"><div class="import-panel-heading"><div><h2>Upload your existing student and guardian list.</h2><p>Bring your roster into ContactLoop with a CSV or Excel spreadsheet.</p></div><span class="import-privacy-note">Private by design · raw file stays in your browser</span></div>${state.error ? `<div class="import-error">${escapeHtml(state.error)}</div>` : ''}<label class="import-dropzone" for="import-file"><span class="import-upload-icon">↑</span><strong>Drag &amp; drop your file here</strong><span>or <u>Browse files</u></span><small>Supported formats: .csv, .xlsx</small><input id="import-file" type="file" accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"></label><button class="template-link" data-download-template>Download ContactLoop Template</button></section>`;
}

export function renderImportMapping(state) {
  const mappings = state.headers.map(header => `<div class="mapping-row"><div><span class="mapping-source">${escapeHtml(header)}</span><small>Source column</small></div><span class="mapping-arrow">→</span><label><span class="sr-only">Map ${escapeHtml(header)}</span><select data-import-mapping="${escapeHtml(header)}"><option value="">Needs review</option>${targetFields.map(([value, label]) => `<option value="${value}" ${state.mapping[header] === value ? 'selected' : ''}>${label}</option>`).join('')}</select></label></div>`).join('');
  return `${renderHeader(state)}<section class="import-panel"><div class="import-panel-heading"><div><h2>Match your columns</h2><p>Review the suggested mappings before we prepare your import.</p></div><span class="import-count">${state.headers.length} source columns</span></div>${state.error ? `<div class="import-error">${escapeHtml(state.error)}</div>` : ''}<div class="mapping-list">${mappings || '<div class="empty-state">No columns found in this file.</div>'}</div><div class="import-actions"><button class="button-secondary" data-import-back>Back</button><button class="button-primary" data-import-continue>Continue to review <span>→</span></button></div></section>`;
}

function rowStatus(row) {
  const label = row.status === 'needs-review' ? 'Needs review' : row.status === 'duplicate' ? 'Possible duplicate' : 'Ready';
  return `<span class="import-status ${row.status}">${label}</span>`;
}

export function renderImportReview(state) {
  const stats = state.stats || { students: 0, guardians: 0, ready: 0, needsReview: 0, duplicates: 0 };
  const rows = (state.rows || []).map((row, index) => `<tr><td><input data-import-edit="${index}:student" value="${escapeHtml(row.student.name)}"></td><td><input data-import-edit="${index}:guardian" value="${escapeHtml(row.guardian.name)}"></td><td><input data-import-edit="${index}:relationship" value="${escapeHtml(row.guardian.relationship)}"></td><td><input data-import-edit="${index}:phone" value="${escapeHtml(row.guardian.phone)}"></td><td><input data-import-edit="${index}:email" value="${escapeHtml(row.guardian.email)}"></td><td>${rowStatus(row)}${row.status === 'duplicate' ? `<select data-import-action="${index}" aria-label="Duplicate action"><option value="import" ${row.action !== 'skip' ? 'selected' : ''}>Import as new</option><option value="skip" ${row.action === 'skip' ? 'selected' : ''}>Skip</option></select>` : ''}${row.issues?.length ? `<small class="import-issue">${escapeHtml(row.issues.join(' '))}</small>` : ''}</td></tr>`).join('');
  return `${renderHeader(state)}<section class="import-panel import-review-panel">${state.error ? `<div class="import-error">${escapeHtml(state.error)}</div>` : ''}<div class="import-panel-heading"><div><h2>Ready to import</h2><p>Check the rows below. We will not write records until you confirm.</p></div><div class="import-summary"><strong>${stats.students} student${stats.students === 1 ? '' : 's'}</strong><strong>${stats.guardians} guardian${stats.guardians === 1 ? '' : 's'}</strong><strong>${stats.needsReview} rows need review</strong></div></div><div class="import-table-wrap"><table class="import-table"><thead><tr><th>Student</th><th>Guardian</th><th>Relationship</th><th>Phone</th><th>Email</th><th>Status</th></tr></thead><tbody>${rows || '<tr><td colspan="6" class="empty-state">No rows found.</td></tr>'}</tbody></table></div><div class="import-actions"><button class="button-secondary" data-import-back ${state.loading ? 'disabled' : ''}>Back</button><button class="button-primary" data-import-submit ${stats.ready === 0 && stats.duplicates === 0 || state.loading ? 'disabled' : ''}>${state.loading ? 'Importing…' : 'Import ready records'} ${state.loading ? '' : '<span>→</span>'}</button></div></section>`;
}

export function renderImportComplete(result) {
  return `<div class="import-complete"><div class="complete-check">✓</div><p class="eyebrow">Import complete</p><h1>${result?.students_imported ?? 0} students imported</h1><p class="complete-secondary">${result?.guardians_imported ?? 0} guardian contacts imported</p><p>Your student list is ready.</p><button class="button-primary" data-view-students>View Students <span>→</span></button></div>`;
}

export function renderImportScreen(state) {
  if (state.step === 'mapping') return renderImportMapping(state);
  if (state.step === 'review') return renderImportReview(state);
  if (state.step === 'complete') return renderImportComplete(state.result);
  return renderImportUpload(state);
}
