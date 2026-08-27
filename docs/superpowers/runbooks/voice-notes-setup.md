# ContactLoop voice notes setup

The active provider is Google Cloud Speech-to-Text V1. The browser only receives a short-lived Google Cloud Storage resumable upload URL. Google credentials must remain in Supabase Edge Function secrets.

## Deploy the three functions

From the ContactLoop project directory:

```bash
npx supabase functions deploy create-voice-upload --project-ref norwecgwrdljbfrbnxbi
npx supabase functions deploy transcribe-voice-note --project-ref norwecgwrdljbfrbnxbi
npx supabase functions deploy get-transcript-status --project-ref norwecgwrdljbfrbnxbi
```

## Required Edge Function secrets

Configure these secrets for the same Supabase project. Do not add them to `.env.local` with a `VITE_` prefix.

```text
GCP_PROJECT_ID=<Google Cloud project id>
GCP_SERVICE_ACCOUNT_EMAIL=<service account email>
GCP_SERVICE_ACCOUNT_PRIVATE_KEY=<private key; replace literal \\n with newlines>
GCS_VOICE_BUCKET=<private GCS bucket name>
CONTACTLOOP_ALLOWED_ORIGIN=http://127.0.0.1:5178
```

The Google service account needs permission to create/read/delete objects in the private bucket and call Speech-to-Text. Create a private Standard Storage bucket, configure CORS for the local/deployed app origins with `PUT`, `POST`, and `OPTIONS` plus `Content-Type`, and add a lifecycle rule to delete `voice-notes/` objects after one day. Enable billing alerts; Speech-to-Text V1 includes a monthly free allowance but billing must be enabled.

The CORS configuration must also expose the `Location` response header because
the browser uses it as the resumable upload URL:

```json
[{"origin":["http://localhost:5178","http://127.0.0.1:5178"],"method":["PUT","POST","OPTIONS"],"responseHeader":["Content-Type","Location"],"maxAgeSeconds":3600}]
```

## Database

Run `supabase/patch-teacher-notes.sql` and `supabase/patch-ai-summary-editor.sql` in the Supabase SQL Editor before testing the feature.

Voice notes are teacher-created context, not phone-call recordings. The app does not send Twilio call IDs or parent call audio to these functions.
