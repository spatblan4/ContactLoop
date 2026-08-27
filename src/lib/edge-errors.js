export function edgeFunctionError(error, name = 'Edge Function') {
  const message = error?.message || '';
  if (/failed to fetch|networkerror|load failed/i.test(message)) {
    return `${name} could not be reached. Check the function URL and CORS allowed origin.`;
  }
  return message || `${name} failed.`;
}
