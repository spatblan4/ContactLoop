export function toastMarkup(toast, escapeHtml = text => String(text ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]))) {
  if (!toast) return '';
  return `<div class="app-toast" role="status"><span>✓</span>${escapeHtml(toast.message)}</div>`;
}
