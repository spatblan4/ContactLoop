export function edgeFunctionError(error, name = 'Edge Function') {
  const message = error?.message || '';
  if (/failed to fetch|failed to send a request to the edge function|networkerror|load failed|cors/i.test(message)) {
    return `${name} could not be reached. Check the function URL and CORS allowed origin.`;
  }
  return message || `${name} failed.`;
}
