import { createClient } from '@supabase/supabase-js';
import { nextAttemptNumber } from './contact-attempts.js';
import { edgeFunctionError } from './edge-errors.js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const hasSupabaseConfig = Boolean(supabaseUrl && supabaseAnonKey);
export const supabase = hasSupabaseConfig ? createClient(supabaseUrl, supabaseAnonKey) : null;

async function invokeEdgeFunction(name, body) {
  if (!supabase) throw new Error('Supabase is not configured.');
  const { data, error } = await supabase.functions.invoke(name, { body });
  if (!error) return data;

  // FunctionsHttpError keeps the actual Response in `context`. Surface the
  // server's JSON message so the UI can tell a configuration problem from an
  // upload or transcription problem.
  let detail = '';
  try {
    const response = error.context;
    if (response?.clone) {
      const payload = await response.clone().json();
      detail = payload?.error || payload?.message || '';
    }
  } catch {
    // Keep the SDK message when the response is not JSON (for example, a CORS
    // or network failure).
  }
  throw new Error(detail || edgeFunctionError(error, name));
}

export async function invokeContactBrief(body) {
  return invokeEdgeFunction('contact-brief-proxy', body);
}

export async function loadContactLoopData() {
  if (!supabase) return { students: [], events: [], followUps: [], setupRequired: true };

  const [studentsResult, eventsResult, followUpsResult, aiBriefsResult] = await Promise.all([
    supabase.from('students').select('id, name, initials, accent, guardians(id, name, relation, phone)').order('name'),
    supabase.from('contact_events').select('id, student_id, guardian_id, call_time, duration_seconds, result, attempt_number, topic, planned_topic, discussed_topics, teacher_note, follow_up_id, provider, provider_call_id, provider_status, started_at, ended_at').order('call_time', { ascending: false }),
    supabase.from('follow_ups').select('id, student_id, guardian_id, due_at, status, contact_event_id').eq('status', 'open').order('due_at'),
    supabase.from('ai_contact_briefs').select('*').neq('status', 'superseded').order('version', { ascending: false }),
  ]);

  const missingBriefTable = aiBriefsResult.error?.code === '42P01' || aiBriefsResult.error?.message?.includes('ai_contact_briefs');
  const firstError = studentsResult.error || eventsResult.error || followUpsResult.error || (missingBriefTable ? null : aiBriefsResult.error);
  if (firstError) throw firstError;

  return {
    students: studentsResult.data ?? [],
    events: eventsResult.data ?? [],
    followUps: followUpsResult.data ?? [],
    aiBriefs: missingBriefTable ? [] : (aiBriefsResult.data ?? []),
    setupRequired: false,
  };
}

export async function createContactEvent({ studentId, guardianId, result, durationSeconds, plannedTopic, discussedTopics, topic, teacherNote, followUpDueAt }) {
  if (!supabase) throw new Error('Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.');

  const { data: attemptEvents, error: countError } = await supabase
    .from('contact_events')
    .select('id, student_id, guardian_id, result, call_time, attempt_number')
    .eq('student_id', studentId)
    .eq('guardian_id', guardianId)
    .order('call_time', { ascending: true });
  if (countError) throw countError;

  const { data: existingFollowUps, error: followUpLookupError } = await supabase
    .from('follow_ups')
    .select('id')
    .eq('student_id', studentId)
    .eq('guardian_id', guardianId)
    .eq('status', 'open')
    .order('due_at')
    .limit(1);
  if (followUpLookupError) throw followUpLookupError;
  const existingFollowUpId = existingFollowUps?.[0]?.id ?? null;

  const { data, error } = await supabase.from('contact_events').insert({
    student_id: studentId,
    guardian_id: guardianId,
    call_time: new Date().toISOString(),
    duration_seconds: durationSeconds ?? null,
    result,
    attempt_number: nextAttemptNumber(attemptEvents ?? [], studentId, guardianId),
    topic: topic || null,
    planned_topic: plannedTopic || null,
    discussed_topics: result === 'Connected' ? (discussedTopics || (plannedTopic ? [plannedTopic] : [])) : [],
    teacher_note: teacherNote || null,
    follow_up_id: existingFollowUpId,
  }).select('id, student_id, guardian_id, call_time, duration_seconds, result, attempt_number, topic, planned_topic, discussed_topics, teacher_note, follow_up_id').single();
  if (error) throw error;

  if (result === 'Connected') {
    if (existingFollowUpId) {
      const { error: closeError } = await supabase.from('follow_ups').update({ status: 'completed', contact_event_id: data.id }).eq('id', existingFollowUpId).eq('status', 'open');
      if (closeError) throw closeError;
    }
    return data;
  }

  if (['No Answer', 'Busy', 'Failed'].includes(result)) {
    let followUpId = existingFollowUpId;
    if (followUpId) {
      const { error: updateError } = await supabase.from('follow_ups').update({ due_at: followUpDueAt, contact_event_id: data.id, status: 'open' }).eq('id', followUpId).eq('status', 'open');
      if (updateError) throw updateError;
    } else {
      const { data: createdFollowUp, error: createFollowUpError } = await supabase.from('follow_ups').insert({ due_at: followUpDueAt, student_id: studentId, guardian_id: guardianId, status: 'open', contact_event_id: data.id }).select('id').single();
      if (createFollowUpError) {
        if (createFollowUpError.code !== '23505') throw createFollowUpError;
        const { data: concurrentFollowUps, error: concurrentLookupError } = await supabase.from('follow_ups').select('id').eq('student_id', studentId).eq('guardian_id', guardianId).eq('status', 'open').order('due_at').limit(1);
        if (concurrentLookupError || !concurrentFollowUps?.[0]) throw concurrentLookupError || new Error('Unable to reuse the open follow-up.');
        followUpId = concurrentFollowUps[0].id;
        const { error: concurrentUpdateError } = await supabase.from('follow_ups').update({ due_at: followUpDueAt, contact_event_id: data.id }).eq('id', followUpId);
        if (concurrentUpdateError) throw concurrentUpdateError;
      } else {
        followUpId = createdFollowUp.id;
      }
    }
    if (!existingFollowUpId && followUpId) {
      const { error: eventLinkError } = await supabase.from('contact_events').update({ follow_up_id: followUpId }).eq('id', data.id);
      if (eventLinkError) throw eventLinkError;
    }
  }
  return data;
}

export async function updateFollowUp(id, updates) {
  if (!supabase) throw new Error('Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.');
  const { error } = await supabase.from('follow_ups').update(updates).eq('id', id);
  if (error) throw error;
}

export async function createStudent({ name, guardianName, relation, phone }) {
  if (!supabase) throw new Error('Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.');
  const initials = name.split(/\s+/).filter(Boolean).map(part => part[0]).join('').slice(0, 2).toUpperCase();
  const { data: student, error: studentError } = await supabase.from('students').insert({ name, initials, accent: 'sage' }).select('id, name, initials, accent').single();
  if (studentError) throw studentError;
  const { error: guardianError } = await supabase.from('guardians').insert({ student_id: student.id, name: guardianName, relation, phone });
  if (guardianError) throw guardianError;
  return student;
}

export async function saveAiContactBrief({ studentId, dateFrom, dateTo, version = 1, status = 'draft', brief }) {
  if (!supabase) throw new Error('Supabase is not configured.');
  const { data, error } = await supabase.from('ai_contact_briefs').insert({
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
  }).select('*').single();
  if (error) throw error;
  return data;
}

export async function updateAiContactBrief(id, { brief, status = 'draft' }) {
  if (!supabase) throw new Error('Supabase is not configured.');
  const { data, error } = await supabase.from('ai_contact_briefs').update({
    status,
    key_topics: brief.key_topics ?? [],
    parent_concerns: brief.parent_concerns ?? [],
    recorded_resolutions: brief.recorded_resolutions ?? [],
    open_items: brief.open_items ?? [],
    suggested_next_step: brief.suggested_next_step ?? null,
    updated_at: new Date().toISOString(),
  }).eq('id', id).select('*').single();
  if (error) throw error;
  return data;
}

export async function supersedeAiContactBrief(id) {
  if (!supabase) throw new Error('Supabase is not configured.');
  const { error } = await supabase.from('ai_contact_briefs').update({ status: 'superseded', updated_at: new Date().toISOString() }).eq('id', id);
  if (error) throw error;
}

export async function approveAiContactBrief(id) {
  if (!supabase) throw new Error('Supabase is not configured.');
  const { data, error } = await supabase.from('ai_contact_briefs').update({ status: 'approved', approved_at: new Date().toISOString(), updated_at: new Date().toISOString() }).eq('id', id).select('*').single();
  if (error) throw error;
  return data;
}

export async function removeAiContactBrief(id) {
  if (!supabase) throw new Error('Supabase is not configured.');
  const { error } = await supabase.from('ai_contact_briefs').delete().eq('id', id);
  if (error) throw error;
}

export async function createTeacherNote({ studentId, content, source = 'voice' }) {
  if (!supabase) throw new Error('Supabase is not configured.');
  if (!content?.trim()) throw new Error('A confirmed note is required.');
  const { data, error } = await supabase.from('teacher_notes').insert({ student_id: studentId, content: content.trim(), source, teacher_confirmed: true }).select('*').single();
  if (error) throw error;
  return data;
}

export async function createVoiceUpload({ studentId, contentType }) {
  return invokeEdgeFunction('create-voice-upload', { student_id: studentId, content_type: contentType });
}

export async function startVoiceTranscription({ studentId, objectKey }) {
  return invokeEdgeFunction('transcribe-voice-note', { student_id: studentId, object_key: objectKey });
}

export async function getVoiceTranscriptStatus({ studentId, jobId, objectKey }) {
  return invokeEdgeFunction('get-transcript-status', { student_id: studentId, job_id: jobId, object_key: objectKey });
}
