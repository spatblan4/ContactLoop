# Google Speech-to-Text Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the blocked Amazon Transcribe voice-note path with Google Speech-to-Text V1 backed by a private, temporary Google Cloud Storage bucket.

**Architecture:** Keep the existing browser payloads and Supabase Edge Function names. `create-voice-upload` creates a GCS resumable upload session, `transcribe-voice-note` starts a Google Speech-to-Text V1 long-running operation, and `get-transcript-status` polls the operation and deletes source audio after successful retrieval.

**Tech Stack:** Supabase Edge Functions, Deno Web Crypto, Google Cloud Storage JSON API, Google Speech-to-Text V1 REST API, Browser MediaRecorder, Node test runner, Vite.

## Global Constraints

- Do not change Twilio call logic.
- Do not expose Google service-account credentials to the browser.
- Do not record or transcribe real parent calls.
- Use Speech-to-Text V1 standard recognition for the monthly free allowance.
- Delete temporary audio after successful transcript retrieval and document one-day lifecycle cleanup.

### Task 1: Provider contract tests

**Files:** Create `tests/google-speech-provider.test.js`; create `src/lib/google-speech-provider.js`.

- [ ] Write tests for the GCS upload content type and Speech-to-Text request payload.
- [ ] Run `node --test tests/google-speech-provider.test.js` and confirm the new module is missing.
- [ ] Implement pure request builders with stable fields: `uploadType=resumable`, `WEBM_OPUS`, `en-US`, and `gs://` URI.
- [ ] Run the focused test and then the existing voice tests.

### Task 2: Secure Edge Function provider

**Files:** Modify `supabase/functions/_shared/voice.ts`; modify `supabase/functions/create-voice-upload/index.ts`; modify `supabase/functions/transcribe-voice-note/index.ts`; modify `supabase/functions/get-transcript-status/index.ts`.

- [ ] Add server-only service-account JWT authentication using Web Crypto.
- [ ] Create GCS resumable upload sessions and return only the session URL/object key.
- [ ] Start and poll Google Speech-to-Text V1 long-running operations.
- [ ] Delete the source object after completion and return retryable JSON errors.

### Task 3: Configuration and documentation

**Files:** Modify `.env.example`; modify `docs/superpowers/runbooks/voice-notes-setup.md`; modify `supabase/config.toml` if required.

- [ ] Document `GCP_PROJECT_ID`, `GCP_SERVICE_ACCOUNT_EMAIL`, `GCP_SERVICE_ACCOUNT_PRIVATE_KEY`, and `GCS_VOICE_BUCKET` as server secrets.
- [ ] Document private bucket lifecycle deletion after one day and billing alerts.
- [ ] Ensure no browser environment file contains server credentials.

### Task 4: Verification

**Files:** No production changes.

- [ ] Run all Node tests.
- [ ] Run `npm run build`.
- [ ] Run available Deno checks for the three voice functions.
- [ ] Report the exact deployment commands and required Supabase secrets without printing secret values.
