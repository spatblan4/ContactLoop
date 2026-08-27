-- Run this once after the existing schema to make follow-ups task-based.

alter table public.follow_ups add column if not exists guardian_id uuid references public.guardians(id) on delete cascade;

update public.follow_ups follow_up
set guardian_id = event.guardian_id
from public.contact_events event
where follow_up.contact_event_id = event.id
  and follow_up.guardian_id is null;

-- Keep the earliest existing open task and close duplicate historical rows.
with ranked as (
  select id, row_number() over (
    partition by student_id, guardian_id
    order by due_at asc, created_at desc, id
  ) as row_number
  from public.follow_ups
  where status = 'open' and guardian_id is not null
)
update public.follow_ups
set status = 'completed'
where id in (select id from ranked where row_number > 1);

create unique index if not exists follow_ups_one_open_per_parent
  on public.follow_ups(student_id, guardian_id)
  where status = 'open';

drop policy if exists "demo update follow ups" on public.follow_ups;
create policy "demo update follow ups" on public.follow_ups for update to anon using (true) with check (true);

drop policy if exists "demo update events" on public.contact_events;
create policy "demo update events" on public.contact_events for update to anon using (true) with check (true);

create or replace function public.sync_follow_up_for_contact_event()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if new.result = 'Connected' and new.ended_at is not null then
    update public.follow_ups
    set status = 'completed', contact_event_id = new.id
    where status = 'open'
      and (
        id = new.follow_up_id
        or (student_id = new.student_id and guardian_id = new.guardian_id)
      );
  elsif new.result in ('No Answer', 'Busy', 'Failed') and new.ended_at is not null then
    insert into public.follow_ups(student_id, guardian_id, due_at, status, contact_event_id)
    values (new.student_id, new.guardian_id, coalesce(new.ended_at, now()) + interval '1 day', 'open', new.id)
    on conflict (student_id, guardian_id) where status = 'open'
    do update set due_at = excluded.due_at, contact_event_id = excluded.contact_event_id;
  end if;
  return new;
end;
$$;

drop trigger if exists sync_follow_up_after_contact_event on public.contact_events;
create trigger sync_follow_up_after_contact_event
after insert or update of result, ended_at on public.contact_events
for each row execute function public.sync_follow_up_for_contact_event();
