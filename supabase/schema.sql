create extension if not exists pgcrypto;

create table if not exists public.students (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  initials text not null,
  accent text not null default 'sage',
  created_at timestamptz not null default now()
);

create table if not exists public.guardians (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  name text not null,
  relation text not null,
  phone text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.follow_ups (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  guardian_id uuid references public.guardians(id) on delete cascade,
  due_at timestamptz not null,
  status text not null default 'open' check (status in ('open', 'completed', 'dismissed')),
  contact_event_id uuid,
  created_at timestamptz not null default now()
);

create table if not exists public.contact_events (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  guardian_id uuid not null references public.guardians(id) on delete restrict,
  call_time timestamptz not null default now(),
  duration_seconds integer,
  result text not null check (result in ('Connected', 'No Answer', 'Busy', 'Failed')),
  attempt_number integer not null check (attempt_number > 0),
  topic text,
  teacher_note text,
  follow_up_id uuid references public.follow_ups(id) on delete set null,
  ended_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.follow_ups drop constraint if exists follow_ups_contact_event_id_fkey;
alter table public.follow_ups add constraint follow_ups_contact_event_id_fkey foreign key (contact_event_id) references public.contact_events(id) on delete set null;

alter table public.students enable row level security;
alter table public.guardians enable row level security;
alter table public.follow_ups enable row level security;
alter table public.contact_events enable row level security;

drop policy if exists "demo read students" on public.students;
drop policy if exists "demo read guardians" on public.guardians;
drop policy if exists "demo read follow ups" on public.follow_ups;
drop policy if exists "demo read events" on public.contact_events;
drop policy if exists "demo insert follow ups" on public.follow_ups;
drop policy if exists "demo insert events" on public.contact_events;
drop policy if exists "demo update follow ups" on public.follow_ups;
drop policy if exists "demo update events" on public.contact_events;
drop policy if exists "demo insert students" on public.students;
drop policy if exists "demo insert guardians" on public.guardians;

create policy "demo read students" on public.students for select to anon using (true);
create policy "demo read guardians" on public.guardians for select to anon using (true);
create policy "demo read follow ups" on public.follow_ups for select to anon using (true);
create policy "demo read events" on public.contact_events for select to anon using (true);
create policy "demo insert follow ups" on public.follow_ups for insert to anon with check (true);
create policy "demo insert events" on public.contact_events for insert to anon with check (true);
create policy "demo update follow ups" on public.follow_ups for update to anon using (true) with check (true);
create policy "demo update events" on public.contact_events for update to anon using (true) with check (true);
create policy "demo insert students" on public.students for insert to anon with check (true);
create policy "demo insert guardians" on public.guardians for insert to anon with check (true);

insert into public.students (id, name, initials, accent) values
  ('11111111-1111-4111-8111-111111111111', 'Emma Johnson', 'EJ', 'sage'),
  ('22222222-2222-4222-8222-222222222222', 'Lucas Smith', 'LS', 'blue'),
  ('33333333-3333-4333-8333-333333333333', 'Noah Williams', 'NW', 'peach'),
  ('44444444-4444-4444-8444-444444444444', 'Ava Chen', 'AC', 'lavender')
on conflict (id) do nothing;

insert into public.guardians (id, student_id, name, relation, phone) values
  ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', '11111111-1111-4111-8111-111111111111', 'Sarah Johnson', 'Mom', '(415) 555-0188'),
  ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', '22222222-2222-4222-8222-222222222222', 'David Smith', 'Dad', '(415) 555-0142'),
  ('cccccccc-cccc-4ccc-8ccc-cccccccccccc', '33333333-3333-4333-8333-333333333333', 'Maya Williams', 'Mom', '(415) 555-0166'),
  ('dddddddd-dddd-4ddd-8ddd-dddddddddddd', '44444444-4444-4444-8444-444444444444', 'Michael Chen', 'Dad', '(415) 555-0113')
on conflict (id) do nothing;

insert into public.contact_events (id, student_id, guardian_id, call_time, duration_seconds, result, attempt_number, topic, teacher_note)
values
  ('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee1', '11111111-1111-4111-8111-111111111111', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', now() - interval '3 days', null, 'No Answer', 1, null, null),
  ('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee2', '11111111-1111-4111-8111-111111111111', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', now() - interval '2 hours', null, 'No Answer', 2, null, null),
  ('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee3', '22222222-2222-4222-8222-222222222222', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', now() - interval '4 hours', 463, 'Connected', 1, 'IEP', 'Dad confirmed Friday at 2 and asked about transportation.'),
  ('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee4', '33333333-3333-4333-8333-333333333333', 'cccccccc-cccc-4ccc-8ccc-cccccccccccc', now() - interval '2 days', 252, 'Connected', 1, 'Behavior', null),
  ('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee5', '33333333-3333-4333-8333-333333333333', 'cccccccc-cccc-4ccc-8ccc-cccccccccccc', now() - interval '2 hours', null, 'Busy', 1, null, null),
  ('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee6', '44444444-4444-4444-8444-444444444444', 'dddddddd-dddd-4ddd-8ddd-dddddddddddd', now() - interval '5 hours', null, 'Failed', 1, null, null)
on conflict (id) do nothing;

insert into public.follow_ups (id, student_id, due_at, status, contact_event_id) values
  ('f1111111-1111-4111-8111-111111111111', '11111111-1111-4111-8111-111111111111', now() + interval '1 day', 'open', 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee2'),
  ('f3333333-3333-4333-8333-333333333333', '33333333-3333-4333-8333-333333333333', now() + interval '1 day', 'open', 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee5')
on conflict (id) do nothing;

update public.contact_events set follow_up_id = 'f1111111-1111-4111-8111-111111111111' where id = 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee2';
update public.contact_events set follow_up_id = 'f3333333-3333-4333-8333-333333333333' where id = 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee5';

update public.follow_ups follow_up
set guardian_id = event.guardian_id
from public.contact_events event
where follow_up.contact_event_id = event.id
  and follow_up.guardian_id is null;

create unique index if not exists follow_ups_one_open_per_parent
  on public.follow_ups(student_id, guardian_id)
  where status = 'open';

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
      and (id = new.follow_up_id or (student_id = new.student_id and guardian_id = new.guardian_id));
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
