export function toastMarkup(toast, escapeHtml = text => String(text ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]))) {
  if (!toast) return '';
  const error = toast.tone === 'error';
  return `<div class="app-toast ${error ? 'error' : ''}" role="status"><span>${error ? '!' : '✓'}</span>${escapeHtml(toast.message)}</div>`;
}
