-- Read-only server-side statistics for the AWS Contact Brief provider.
-- The AI service uses the service role key; the browser does not call this RPC.

create or replace function public.get_contact_stats(
  p_student_id uuid,
  p_from timestamptz,
  p_to timestamptz
)
returns jsonb
language sql
stable
security invoker
as $$
  select jsonb_build_object(
    'total_attempts', count(*) filter (where result in ('Connected', 'No Answer', 'Busy', 'Failed'))::int,
    'successful_conversations', count(*) filter (where result = 'Connected')::int,
    'no_answer', count(*) filter (where result = 'No Answer')::int,
    'busy', count(*) filter (where result = 'Busy')::int,
    'failed', count(*) filter (where result = 'Failed')::int,
    'last_successful_contact', max(call_time) filter (where result = 'Connected'),
    'open_follow_ups', (
      select count(*)::int
      from public.follow_ups follow_up
      where follow_up.student_id = p_student_id
        and follow_up.status = 'open'
    )
  )
  from public.contact_events event
  where event.student_id = p_student_id
    and event.call_time >= p_from
    and event.call_time < p_to;
$$;

revoke all on function public.get_contact_stats(uuid, timestamptz, timestamptz) from public, anon, authenticated;
grant execute on function public.get_contact_stats(uuid, timestamptz, timestamptz) to service_role;
