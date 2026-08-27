const encoder = new TextEncoder();

function decodeBase64(value) {
  try {
    return Uint8Array.from(atob(value), character => character.charCodeAt(0));
  } catch {
    return null;
  }
}

export async function validateTwilioSignature({ url, formData, signature, authToken }) {
  if (!signature || !authToken) return false;

  const sortedParameters = [...formData.entries()]
    .map(([name, value]) => [name, String(value)])
    .sort(([left], [right]) => (left < right ? -1 : left > right ? 1 : 0));
  const payload = sortedParameters.reduce(
    (result, [name, value]) => `${result}${name}${value}`,
    url,
  );
  const signatureBytes = decodeBase64(signature);
  if (!signatureBytes) return false;

  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(authToken),
    { name: 'HMAC', hash: 'SHA-1' },
    false,
    ['verify'],
  );
  return crypto.subtle.verify('HMAC', key, signatureBytes, encoder.encode(payload));
}
