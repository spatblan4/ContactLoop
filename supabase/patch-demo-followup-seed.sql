-- Correct the Demo-only seed timeline.
-- Noah's successful contact closes one cycle; the later Busy call begins a new open cycle.
-- This patch intentionally targets only the fixed demo seed IDs and does not change teacher-created records.

update public.contact_events
set call_time = now() - interval '2 days',
    attempt_number = 1
where id = 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee4';

update public.contact_events
set call_time = now() - interval '2 hours',
    attempt_number = 1
where id = 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee5';

update public.follow_ups
set status = 'open',
    due_at = now() + interval '1 day',
    contact_event_id = 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee5'
where id = 'f3333333-3333-4333-8333-333333333333';
