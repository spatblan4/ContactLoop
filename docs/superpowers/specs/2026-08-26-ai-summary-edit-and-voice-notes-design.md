# AI Contact Summary Edit and Voice Notes Design

## Goal

让老师可以在当前 AI Contact Summary 卡片内编辑、审核和删除 AI 内容，并通过浏览器录制一段仅由老师主动添加的短语音备注，经 Amazon S3、Amazon Transcribe 和教师确认后保存为 teacher-approved note，再由老师决定是否重新生成 Summary。

## Scope

本次功能包含两个边界清晰的子系统：

1. AI Summary review：编辑、增删条目、保存、批准、重新生成和移除。
2. Voice context：录音、临时上传、批量转录、transcript 审核、保存 note 和可选重新生成。

不包含真实家长电话录音、实时转录、voice-to-text streaming、OpenAI API 或自动批准 AI 内容。

## Architecture

```text
Browser MediaRecorder
        |
        v
Supabase Edge Function: create-voice-upload
        |
        v
Private S3 bucket (temporary audio)
        |
        v
Supabase Edge Function: transcribe-voice-note
        |
        v
Amazon Transcribe batch job
        |
        v
Transcript Review modal
        |
        v
Supabase teacher_notes (teacher_confirmed = true)
        |
        v
Optional AWS Contact Brief regeneration
```

The browser never receives AWS access keys. The S3 bucket is private. The uploaded audio is temporary and must have a lifecycle rule that deletes objects after one day. Long-term application data is the teacher-confirmed text note, not the audio file.

The existing Twilio, Supabase call-status, contact-event, and AWS Strands provider logic remains unchanged except for the new note data needed by the existing read-only Contact Brief tools.

## AI Summary Review UX

The default card continues to show the existing Supabase-derived stats and the AI narrative sections:

- Key Topics
- Parent Concerns
- Recorded Resolutions
- Open Items
- Suggested Next Step

The default actions become `Edit`, `Add by voice`, and `Approve summary`. `Remove summary` moves to a `•••` menu together with `Regenerate summary`.

When Edit is selected, the same card enters an inline editing state. Each list supports editing an existing item, deleting an item, and adding a new item. Suggested Next Step uses an editable text input. Edit mode actions are `Cancel` and `Save changes`.

Saving persists the teacher-edited content to Supabase and marks the narrative as teacher-reviewed content. The numeric stats are never editable in this UI and continue to come from Supabase.

Generated content starts in `Needs Teacher Review`. Approving sets `teacher_approved = true` and `approved_at`. Approved content displays `Teacher Approved` and can be consumed by Meeting Brief. Removing clears the saved brief for that student/range after confirmation. Regenerate creates a new pending result and does not silently approve it.

## Voice Context UX

`Add by voice` opens a modal titled `Add context by voice` with the text:

> Record a short note to add context to this student's communication history.

The modal has `Start recording`, a visible elapsed timer, `Stop recording`, and `Cancel`. It records only while the teacher explicitly starts recording. It does not hook into the Twilio call stream and does not record the parent call.

After transcription, the modal shows an editable `Voice transcript` textarea. The teacher can edit the text, cancel, or choose `Save note`. The transcript is not inserted into AI Summary automatically.

After a successful save, show `New context saved.` and ask `Update AI Contact Summary with this note?` with `Update Summary` and `Not now`. Only `Update Summary` calls the AWS Contact Brief provider again. If regenerated content adds an evidence-backed item, render a temporary `NEW` marker; the teacher still must approve the new result.

## Data Model

Add a persisted brief table with one current record per student and reporting range:

```text
ai_contact_briefs
- id
- student_id
- date_from
- date_to
- key_topics jsonb
- parent_concerns jsonb
- recorded_resolutions jsonb
- open_items jsonb
- suggested_next_step text
- teacher_approved boolean
- approved_at timestamptz
- created_at timestamptz
- updated_at timestamptz
```

Add teacher-confirmed notes:

```text
teacher_notes
- id
- student_id
- contact_event_id nullable
- teacher_note text
- voice_transcript text nullable
- note_source text (`typed` or `voice`)
- teacher_confirmed boolean
- created_at timestamptz
```

The existing Contact Brief RPC remains authoritative for all numbers. The AI provider tools may read contact stats, approved notes/topics, and open follow-ups, but the model does not calculate or infer counts.

## Server-Side Voice Flow

1. The browser sends only authenticated student context and requested audio metadata to a Supabase Edge Function.
2. The Edge Function returns a short-lived presigned S3 upload URL. AWS credentials remain server-side.
3. The browser uploads the Blob to the private S3 bucket.
4. The browser calls the transcription Edge Function with the temporary object key.
5. The server starts an Amazon Transcribe batch job with an output location controlled by the server, polls until completion, validates the returned transcript, and returns text only.
6. The browser displays the transcript for teacher editing.
7. On `Save note`, the browser writes the edited, teacher-confirmed note to Supabase through the existing authenticated data path.
8. Temporary audio and raw transcript artifacts are deleted or expire automatically. No audio URL or provider ID is shown in the UI.

If recording is unsupported, permission is denied, upload fails, or transcription fails, the modal shows a recoverable error and does not create a teacher note.

## Human-in-the-Loop Rules

- AI output always starts as pending review.
- Voice transcript is never treated as final note content before teacher confirmation.
- Teacher edits are persisted as teacher-reviewed content.
- `Update Summary` is an explicit action after saving voice context.
- Empty or unsupported evidence produces an empty section or a clear no-recorded-information message.
- The model cannot create parent concerns, resolutions, topics, or open items without database evidence.

## Privacy and Security

- No real parent call audio is recorded or transcribed.
- S3 bucket is private and uses short-lived presigned URLs.
- Browser bundle contains no AWS credentials, service-role key, or Transcribe credentials.
- Temporary audio objects expire after one day.
- Printed or displayed summaries do not expose S3 keys, Twilio SIDs, internal IDs, or technical errors.
- RLS policies restrict notes and briefs to the authenticated teacher/workspace.

## Testing and Acceptance

Unit tests must cover:

- Editing, adding, deleting, and saving each summary section.
- Cancel restoring the pre-edit state.
- Approval metadata and pending/approved display state.
- Menu actions for regenerate and remove.
- Voice state transitions: idle, recording, stopped, transcribing, review, saved, and error.
- A transcript cannot be persisted unless `teacher_confirmed = true`.
- Saving a voice note does not automatically regenerate the summary.
- Regeneration uses the latest approved note and leaves the new result pending.
- Numeric stats remain the Supabase-provided values.

End-to-end acceptance:

1. Generate a summary for a student.
2. Edit one topic, add one concern, delete one resolution, and change the next step.
3. Save, refresh, and verify all edits remain.
4. Approve and verify `Teacher Approved` plus approval metadata.
5. Start and stop a short voice note.
6. Edit the returned transcript and save it.
7. Refresh and verify the note is teacher-confirmed.
8. Choose `Update Summary` and verify the new result is pending review and contains only evidence from saved data.

