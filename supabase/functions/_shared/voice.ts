import { googleOperationPath } from './google-operation.ts';

const projectId = Deno.env.get('GCP_PROJECT_ID');
const serviceAccountEmail = Deno.env.get('GCP_SERVICE_ACCOUNT_EMAIL');
const privateKey = Deno.env.get('GCP_SERVICE_ACCOUNT_PRIVATE_KEY')?.replace(/\\n/g, '\n');
const bucket = Deno.env.get('GCS_VOICE_BUCKET');

const configuredOrigins = (Deno.env.get('CONTACTLOOP_ALLOWED_ORIGIN') || '*').split(/\s*,\s*/).filter(Boolean);

export function corsHeadersFor(request?: Request) {
  const requestOrigin = request?.headers.get('origin') || '';
  const allowOrigin = configuredOrigins.includes('*')
    ? '*'
    : (configuredOrigins.includes(requestOrigin) ? requestOrigin : configuredOrigins[0] || '*');
  return {
  'Access-Control-Allow-Origin': allowOrigin,
  'Vary': 'Origin',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  };
}

function base64Url(value: Uint8Array | string) {
  const bytes = typeof value === 'string' ? new TextEncoder().encode(value) : value;
  let binary = '';
  bytes.forEach(byte => { binary += String.fromCharCode(byte); });
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function fromBase64(value: string) {
  const normalized = value.replace(/-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\s/g, '').replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
  const binary = atob(padded);
  return Uint8Array.from(binary, character => character.charCodeAt(0));
}

function requireGoogleConfig() {
  if (!projectId || !serviceAccountEmail || !privateKey || !bucket) throw new Error('Google voice transcription service is not configured.');
  return { projectId, serviceAccountEmail, privateKey, bucket };
}

let cachedToken: { value: string; expiresAt: number } | null = null;

async function googleAccessToken() {
  const config = requireGoogleConfig();
  if (cachedToken && cachedToken.expiresAt > Date.now() + 60_000) return cachedToken.value;
  const issuedAt = Math.floor(Date.now() / 1000);
  const header = base64Url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const claim = base64Url(JSON.stringify({ iss: config.serviceAccountEmail, scope: 'https://www.googleapis.com/auth/cloud-platform', aud: 'https://oauth2.googleapis.com/token', iat: issuedAt, exp: issuedAt + 3600 }));
  const key = await crypto.subtle.importKey('pkcs8', fromBase64(config.privateKey), { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
  const signature = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(`${header}.${claim}`));
  const assertion = `${header}.${claim}.${base64Url(new Uint8Array(signature))}`;
  const response = await fetch('https://oauth2.googleapis.com/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer', assertion }) });
  const payload = await response.json();
  if (!response.ok || !payload.access_token) throw new Error(payload.error_description || 'Google authentication failed.');
  cachedToken = { value: payload.access_token, expiresAt: Date.now() + Number(payload.expires_in || 3600) * 1000 };
  return payload.access_token;
}

function hex(bytes: ArrayBuffer) {
  return [...new Uint8Array(bytes)].map(byte => byte.toString(16).padStart(2, '0')).join('');
}

async function sha256(value: string) {
  return hex(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)));
}

function encodePath(value: string) {
  return value.split('/').map(segment => encodeURIComponent(segment)).join('/');
}

async function signedUploadUrl(objectKey: string, contentType: string) {
  const config = requireGoogleConfig();
  const now = new Date();
  const date = now.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  const shortDate = date.slice(0, 8);
  const credential = `${config.serviceAccountEmail}/${shortDate}/auto/storage/goog4_request`;
  const canonicalUri = `/${encodePath(config.bucket)}/${encodePath(objectKey)}`;
  const canonicalQuery = [
    ['X-Goog-Algorithm', 'GOOG4-RSA-SHA256'],
    ['X-Goog-Credential', credential],
    ['X-Goog-Date', date],
    ['X-Goog-Expires', '900'],
    ['X-Goog-SignedHeaders', 'content-type;host'],
  ].map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`).join('&');
  const canonicalHeaders = `content-type:${contentType}\nhost:storage.googleapis.com\n`;
  const canonicalRequest = ['PUT', canonicalUri, canonicalQuery, canonicalHeaders, 'content-type;host', 'UNSIGNED-PAYLOAD'].join('\n');
  const stringToSign = ['GOOG4-RSA-SHA256', date, `${shortDate}/auto/storage/goog4_request`, await sha256(canonicalRequest)].join('\n');
  const key = await crypto.subtle.importKey('pkcs8', fromBase64(config.privateKey), { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
  const signature = hex(await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(stringToSign)));
  return `https://storage.googleapis.com${canonicalUri}?${canonicalQuery}&X-Goog-Signature=${signature}`;
}

async function googleFetch(url: string, init: RequestInit = {}) {
  const token = await googleAccessToken();
  const response = await fetch(url, { ...init, headers: { Authorization: `Bearer ${token}`, ...(init.headers || {}) } });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error?.message || payload.error_description || `Google API returned ${response.status}.`);
  return payload;
}

export function json(body: unknown, status = 200, request?: Request) {
  return new Response(JSON.stringify(body), { status, headers: { ...corsHeadersFor(request), 'Content-Type': 'application/json' } });
}

export function requireBucket() { return requireGoogleConfig().bucket; }

export async function createUploadUrl(objectKey: string, contentType: string) {
  return { uploadUrl: await signedUploadUrl(objectKey, contentType), objectKey };
}

export async function startJob(objectKey: string, _studentId: string) {
  const config = requireGoogleConfig();
  const payload = await googleFetch('https://speech.googleapis.com/v1/speech:longrunningrecognize', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ config: { encoding: 'WEBM_OPUS', languageCode: 'en-US', model: 'latest_long' }, audio: { uri: `gs://${config.bucket}/${objectKey}` } }) });
  if (!payload.name) throw new Error('Google did not return a transcription operation.');
  return payload.name as string;
}

async function deleteObject(objectKey: string) {
  const config = requireGoogleConfig();
  await googleFetch(`https://storage.googleapis.com/storage/v1/b/${encodeURIComponent(config.bucket)}/o/${encodeURIComponent(objectKey)}`, { method: 'DELETE' });
}

export async function transcriptStatus(jobId: string, objectKey: string) {
  const operationPath = googleOperationPath(jobId);
  const payload = await googleFetch(`https://speech.googleapis.com/v1/${operationPath}`);
  if (!payload.done) return { status: 'transcribing' as const };
  if (payload.error) return { status: 'failed' as const };
  const transcript = (payload.response?.results || []).flatMap((result: { alternatives?: { transcript?: string }[] }) => result.alternatives?.[0]?.transcript || '').join(' ').trim();
  if (objectKey.startsWith('voice-notes/')) await deleteObject(objectKey);
  return { status: 'completed' as const, transcript };
}
