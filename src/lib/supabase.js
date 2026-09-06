// Compatibility facade: the UI keeps importing from this module, but every data
// operation now goes through the fetch-based FastAPI client in ./api/.
// The `supabase` export remains only for Supabase Auth (src/lib/auth.js) and
// the Twilio telephony provider when VITE_SUPABASE_URL is configured.
import { createClient } from '@supabase/supabase-js';
import { APP_MODE } from './app-config.js';
import { hasBackendConfig } from './api/client.js';
import * as studentsApi from './api/students.js';
import * as guardiansApi from './api/guardians.js';
import * as contactEventsApi from './api/contact-events.js';
import * as followUpsApi from './api/follow-ups.js';
import * as teacherNotesApi from './api/teacher-notes.js';
import * as aiBriefsApi from './api/ai-briefs.js';
import * as dataApi from './api/data.js';
import * as importsApi from './api/imports.js';
import * as voiceApi from './api/voice.js';
import { generateContactBrief } from './api/contact-brief.js';

const supabaseUrl = import.meta.env?.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env?.VITE_SUPABASE_ANON_KEY;

export const hasSupabaseConfig = Boolean(supabaseUrl && supabaseAnonKey);

let supabaseClient = null;
if (hasSupabaseConfig) {
  try {
    supabaseClient = createClient(supabaseUrl, supabaseAnonKey);
  } catch {
    supabaseClient = null;
  }
}
export const supabase = supabaseClient;

export { hasBackendConfig };

export function shouldUseOwnerDerivedStudentInsert({ appMode = APP_MODE, session } = {}) {
  return appMode === 'authenticated' || Boolean(session);
}

export async function loadContactLoopData() {
  if (!hasBackendConfig()) {
    return { students: [], events: [], followUps: [], teacherNotes: [], aiBriefs: [], setupRequired: true };
  }
  const data = (await dataApi.loadContactLoopData()) ?? {};
  return {
    students: data.students ?? [],
    events: data.events ?? [],
    followUps: data.follow_ups ?? [],
    teacherNotes: data.teacher_notes ?? [],
    aiBriefs: data.ai_briefs ?? [],
    setupRequired: false,
  };
}

export async function importStudents(payload) {
  const result = await importsApi.importStudents({
    students: payload?.students ?? [],
    guardians: payload?.guardians ?? [],
  });
  return {
    students_imported: result?.imported_students ?? 0,
    guardians_imported: result?.imported_guardians ?? 0,
  };
}

export async function createContactEvent({ studentId, guardianId, result, durationSeconds, plannedTopic, discussedTopics, topic, teacherNote, followUpDueAt }) {
  return contactEventsApi.createContactEvent({
    student_id: studentId,
    guardian_id: guardianId,
    result,
    duration_seconds: durationSeconds ?? null,
    planned_topic: plannedTopic || null,
    discussed_topics: result === 'Connected' ? (discussedTopics || (plannedTopic ? [plannedTopic] : [])) : [],
    topic: topic || null,
    teacher_note: teacherNote || null,
    follow_up_due_at: followUpDueAt ?? null,
  });
}

export async function updateFollowUp(id, updates) {
  return followUpsApi.updateFollowUp(id, updates);
}

export async function createStudent({ name, guardianName, relation, phone, guardians: suppliedGuardians }) {
  const guardians = suppliedGuardians?.length ? suppliedGuardians : [{ name: guardianName, relation, phone }];
  const trimmed = name.trim();
  const parts = trimmed.split(/\s+/);
  return studentsApi.createStudent({
    name: trimmed,
    first_name: parts.slice(0, -1).join(' ') || parts[0],
    last_name: parts.at(-1) || '',
    guardians: guardians.map(guardian => ({ name: guardian.name, relation: guardian.relation, phone: guardian.phone })),
  });
}

export async function updateStudent({ studentId, guardianId, name, guardianName, relation, phone }) {
  if (!studentId || !guardianId) throw new Error('Student and guardian ids are required.');
  await studentsApi.updateStudent(studentId, { name });
  await guardiansApi.updateGuardian(guardianId, { name: guardianName, relation, phone });
}

export async function deleteStudent(studentId) {
  const id = String(studentId || '').trim();
  if (!id) throw new Error('Student id is required.');
  await studentsApi.deleteStudent(id);
}

export async function saveAiContactBrief({ studentId, dateFrom, dateTo, version = 1, status = 'draft', brief }) {
  return aiBriefsApi.createAiBrief({
    student_id: studentId,
    date_from: dateFrom,
    date_to: dateTo,
    version,
    status,
    key_topics: brief.key_topics ?? [],
    parent_concerns: brief.parent_concerns ?? [],
    recorded_resolutions: brief.recorded_resolutions ?? [],
    open_items: brief.open_items ?? [],
    suggested_next_step: brief.suggested_next_step ?? null,
  });
}

export async function updateAiContactBrief(id, { brief, status = 'draft' }) {
  return aiBriefsApi.updateAiBrief(id, {
    status,
    key_topics: brief.key_topics ?? [],
    parent_concerns: brief.parent_concerns ?? [],
    recorded_resolutions: brief.recorded_resolutions ?? [],
    open_items: brief.open_items ?? [],
    suggested_next_step: brief.suggested_next_step ?? null,
  });
}

export async function supersedeAiContactBrief(id) {
  return aiBriefsApi.supersedeAiBrief(id);
}

export async function approveAiContactBrief(id) {
  return aiBriefsApi.approveAiBrief(id);
}

export async function removeAiContactBrief(id) {
  return aiBriefsApi.deleteAiBrief(id);
}

export async function createTeacherNote({ studentId, content, source = 'voice' }) {
  if (!content?.trim()) throw new Error('A confirmed note is required.');
  return teacherNotesApi.createTeacherNote({ student_id: studentId, content: content.trim(), source });
}

export async function createVoiceUpload({ studentId, contentType }) {
  const result = await voiceApi.createVoiceUpload({ student_id: studentId, content_type: contentType });
  return { uploadUrl: result?.upload_url, objectKey: result?.object_key };
}

export async function startVoiceTranscription({ studentId, objectKey }) {
  const result = await voiceApi.startVoiceTranscription({ student_id: studentId, object_key: objectKey });
  return { jobId: result?.job_id };
}

export async function getVoiceTranscriptStatus({ studentId, jobId, objectKey }) {
  const result = await voiceApi.getVoiceTranscription(jobId);
  return { status: result?.status, transcript: result?.transcript };
}

export async function invokeContactBrief(body) {
  return generateContactBrief(body);
}

export function listGuardians({ studentId } = {}) {
  return guardiansApi.listGuardians({ student_id: studentId });
}

export function createGuardian(guardian) {
  return guardiansApi.createGuardian(guardian);
}

export function updateGuardian(id, updates) {
  return guardiansApi.updateGuardian(id, updates);
}

export function deleteGuardian(id) {
  return guardiansApi.deleteGuardian(id);
}

export function updateContactEvent(id, updates) {
  return contactEventsApi.updateContactEvent(id, updates);
}

export function deleteContactEvent(id) {
  return contactEventsApi.deleteContactEvent(id);
}

export function listFollowUps({ status, studentId } = {}) {
  return followUpsApi.listFollowUps({ status, student_id: studentId });
}

export function createFollowUp(followUp) {
  return followUpsApi.createFollowUp(followUp);
}

export function deleteFollowUp(id) {
  return followUpsApi.deleteFollowUp(id);
}

export function updateTeacherNote(id, updates) {
  return teacherNotesApi.updateTeacherNote(id, updates);
}

export function deleteTeacherNote(id) {
  return teacherNotesApi.deleteTeacherNote(id);
}
