-- Apply only to the disposable Demo Supabase project.
-- Enables the student edit and delete actions used by the public Demo app.

alter table public.students enable row level security;
alter table public.guardians enable row level security;
alter table public.follow_ups enable row level security;
alter table public.contact_events enable row level security;

drop policy if exists "demo update students" on public.students;
drop policy if exists "demo update guardians" on public.guardians;
drop policy if exists "demo delete students" on public.students;
drop policy if exists "demo delete guardians" on public.guardians;
drop policy if exists "demo delete follow ups" on public.follow_ups;
drop policy if exists "demo delete events" on public.contact_events;

create policy "demo update students" on public.students
  for update to anon using (true) with check (true);

create policy "demo update guardians" on public.guardians
  for update to anon using (true) with check (true);

create policy "demo delete students" on public.students
  for delete to anon using (true);

create policy "demo delete guardians" on public.guardians
  for delete to anon using (true);

create policy "demo delete follow ups" on public.follow_ups
  for delete to anon using (true);

create policy "demo delete events" on public.contact_events
  for delete to anon using (true);

do $$
begin
  if to_regclass('public.teacher_notes') is not null then
    execute 'drop policy if exists "demo delete teacher notes" on public.teacher_notes';
    execute 'create policy "demo delete teacher notes" on public.teacher_notes for delete to anon using (true)';
  end if;
  if to_regclass('public.ai_contact_briefs') is not null then
    execute 'drop policy if exists "demo delete ai briefs" on public.ai_contact_briefs';
    execute 'create policy "demo delete ai briefs" on public.ai_contact_briefs for delete to anon using (true)';
  end if;
end;
$$;
