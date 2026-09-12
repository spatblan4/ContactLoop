export function toastMarkup(toast, escapeHtml) {
  if (!toast) return '';
  return `<div class="app-toast" role="status"><span>✓</span>${escapeHtml(toast.message)}</div>`;
}
