# Google Speech-to-Text voice-note provider

## Goal

Replace the blocked Amazon Transcribe call used for teacher voice notes with Google Cloud Speech-to-Text V1, while preserving the existing ContactLoop voice-note review flow and leaving Twilio, Supabase data, Strands, and Bedrock logic unchanged.

## Architecture

The browser continues to record a teacher-only note with `MediaRecorder`. A Supabase Edge Function issues a short-lived upload URL for a private Google Cloud Storage bucket. A second Edge Function starts a Google Speech-to-Text V1 long-running recognition job against the uploaded object, and the existing polling endpoint returns the transcript for teacher review. After a successful transcript read, the source audio is deleted; a one-day lifecycle rule is the fallback cleanup.

```text
MediaRecorder
  -> create-voice-upload (Supabase Edge Function)
  -> private Google Cloud Storage object
  -> transcribe-voice-note (Google Speech-to-Text V1 long-running operation)
  -> get-transcript-status (poll)
  -> teacher edits and confirms transcript
  -> teacher_notes in Supabase
```

## Provider boundary

- Keep the browser-facing function names and payloads stable: `create-voice-upload`, `transcribe-voice-note`, and `get-transcript-status`.
- Replace only the implementation behind those functions and the shared voice helper.
- Remove AWS Transcribe calls from the active voice-note path, but do not touch Twilio or AI Contact Brief code.
- Keep all Google credentials in Supabase Edge Function secrets. No credential, signed upload secret, or service-account JSON is sent to the browser.

## Storage and privacy

- Use a private, single-region GCS bucket with standard storage.
- Use object keys scoped by student and a random identifier.
- Delete the source audio after a successful transcript response.
- Configure a one-day lifecycle deletion rule as a fallback.
- Do not record or transcribe real parent calls; this path remains teacher-initiated voice context only.

## API behavior

- `create-voice-upload` returns an upload URL and object key.
- `transcribe-voice-note` accepts the object key and returns a job identifier.
- `get-transcript-status` returns `transcribing`, `completed` with transcript, or `failed`.
- Existing UI states remain `Uploading`, `Transcribing`, `Voice transcript`, retry, cancel, and teacher-confirmed save.
- A failed provider request must return a readable error and must not leave the UI in an endless loading state.

## Cost choice

Use Google Speech-to-Text V1 standard recognition so the account receives the published monthly free allowance for the first 60 minutes, subject to Google Cloud billing and quota terms. Add setup documentation for billing alerts and the bucket lifecycle rule.

## Verification

- Unit-test provider response mapping and error states.
- Build the Vite app.
- Type/check Edge Function source where tooling is available.
- Manually verify: record a short teacher note, upload, poll, edit transcript, save, refresh, and confirm the note remains in Supabase.
