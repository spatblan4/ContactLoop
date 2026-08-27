-- Apply this migration to the authenticated trial / production Supabase project.
-- Demo projects may continue using the original demo policies and seed data.

alter table public.students add column if not exists teacher_id uuid references auth.users(id) on delete cascade;
alter table public.students add column if not exists first_name text;
alter table public.students add column if not exists last_name text;
alter table public.guardians add column if not exists email text;
alter table public.guardians add column if not exists preferred_contact_method text;
alter table public.guardians alter column phone drop not null;

create index if not exists students_teacher_name_idx on public.students(teacher_id, name);
create index if not exists guardians_phone_idx on public.guardians(phone);

drop policy if exists "demo read students" on public.students;
drop policy if exists "demo insert students" on public.students;
drop policy if exists "demo update students" on public.students;
drop policy if exists "demo delete students" on public.students;
drop policy if exists "demo read guardians" on public.guardians;
drop policy if exists "demo insert guardians" on public.guardians;
drop policy if exists "demo update guardians" on public.guardians;
drop policy if exists "demo delete guardians" on public.guardians;
drop policy if exists "demo read follow ups" on public.follow_ups;
drop policy if exists "demo insert follow ups" on public.follow_ups;
drop policy if exists "demo update follow ups" on public.follow_ups;
drop policy if exists "demo read events" on public.contact_events;
drop policy if exists "demo insert events" on public.contact_events;
drop policy if exists "demo update events" on public.contact_events;

create policy "teachers read own students" on public.students for select to authenticated using (teacher_id = auth.uid());
create policy "teachers insert own students" on public.students for insert to authenticated with check (teacher_id = auth.uid());
create policy "teachers update own students" on public.students for update to authenticated using (teacher_id = auth.uid()) with check (teacher_id = auth.uid());
create policy "teachers delete own students" on public.students for delete to authenticated using (teacher_id = auth.uid());

create policy "teachers read own guardians" on public.guardians for select to authenticated using (exists (select 1 from public.students where students.id = guardians.student_id and students.teacher_id = auth.uid()));
create policy "teachers insert own guardians" on public.guardians for insert to authenticated with check (exists (select 1 from public.students where students.id = guardians.student_id and students.teacher_id = auth.uid()));
create policy "teachers update own guardians" on public.guardians for update to authenticated using (exists (select 1 from public.students where students.id = guardians.student_id and students.teacher_id = auth.uid())) with check (exists (select 1 from public.students where students.id = guardians.student_id and students.teacher_id = auth.uid()));
create policy "teachers delete own guardians" on public.guardians for delete to authenticated using (exists (select 1 from public.students where students.id = guardians.student_id and students.teacher_id = auth.uid()));

create policy "teachers read own follow ups" on public.follow_ups for select to authenticated using (exists (select 1 from public.students where students.id = follow_ups.student_id and students.teacher_id = auth.uid()));
create policy "teachers insert own follow ups" on public.follow_ups for insert to authenticated with check (exists (select 1 from public.students where students.id = follow_ups.student_id and students.teacher_id = auth.uid()));
create policy "teachers update own follow ups" on public.follow_ups for update to authenticated using (exists (select 1 from public.students where students.id = follow_ups.student_id and students.teacher_id = auth.uid())) with check (exists (select 1 from public.students where students.id = follow_ups.student_id and students.teacher_id = auth.uid()));

create policy "teachers read own events" on public.contact_events for select to authenticated using (exists (select 1 from public.students where students.id = contact_events.student_id and students.teacher_id = auth.uid()));
create policy "teachers insert own events" on public.contact_events for insert to authenticated with check (exists (select 1 from public.students where students.id = contact_events.student_id and students.teacher_id = auth.uid()));
create policy "teachers update own events" on public.contact_events for update to authenticated using (exists (select 1 from public.students where students.id = contact_events.student_id and students.teacher_id = auth.uid())) with check (exists (select 1 from public.students where students.id = contact_events.student_id and students.teacher_id = auth.uid()));

do $$
begin
  if to_regclass('public.ai_contact_briefs') is not null then
    execute 'drop policy if exists "demo read ai briefs" on public.ai_contact_briefs';
    execute 'drop policy if exists "demo insert ai briefs" on public.ai_contact_briefs';
    execute 'drop policy if exists "demo update ai briefs" on public.ai_contact_briefs';
    execute 'drop policy if exists "demo delete ai briefs" on public.ai_contact_briefs';
    execute 'create policy "teachers read own ai briefs" on public.ai_contact_briefs for select to authenticated using (exists (select 1 from public.students where students.id = ai_contact_briefs.student_id and students.teacher_id = auth.uid()))';
    execute 'create policy "teachers insert own ai briefs" on public.ai_contact_briefs for insert to authenticated with check (exists (select 1 from public.students where students.id = ai_contact_briefs.student_id and students.teacher_id = auth.uid()))';
    execute 'create policy "teachers update own ai briefs" on public.ai_contact_briefs for update to authenticated using (exists (select 1 from public.students where students.id = ai_contact_briefs.student_id and students.teacher_id = auth.uid())) with check (exists (select 1 from public.students where students.id = ai_contact_briefs.student_id and students.teacher_id = auth.uid()))';
    execute 'create policy "teachers delete own ai briefs" on public.ai_contact_briefs for delete to authenticated using (exists (select 1 from public.students where students.id = ai_contact_briefs.student_id and students.teacher_id = auth.uid()))';
  end if;
  if to_regclass('public.teacher_notes') is not null then
    execute 'drop policy if exists "demo read teacher notes" on public.teacher_notes';
    execute 'drop policy if exists "demo insert teacher notes" on public.teacher_notes';
    execute 'drop policy if exists "demo update teacher notes" on public.teacher_notes';
    execute 'create policy "teachers read own notes" on public.teacher_notes for select to authenticated using (exists (select 1 from public.students where students.id = teacher_notes.student_id and students.teacher_id = auth.uid()))';
    execute 'create policy "teachers insert own notes" on public.teacher_notes for insert to authenticated with check (teacher_confirmed = true and exists (select 1 from public.students where students.id = teacher_notes.student_id and students.teacher_id = auth.uid()))';
    execute 'create policy "teachers update own notes" on public.teacher_notes for update to authenticated using (exists (select 1 from public.students where students.id = teacher_notes.student_id and students.teacher_id = auth.uid())) with check (teacher_confirmed = true and exists (select 1 from public.students where students.id = teacher_notes.student_id and students.teacher_id = auth.uid()))';
  end if;
end;
$$;

create or replace function public.import_students(p_students jsonb, p_guardians jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
  current_teacher_id uuid := auth.uid();
  student_record jsonb;
  guardian_record jsonb;
  created_student_id uuid;
  students_imported integer := 0;
  guardians_imported integer := 0;
begin
  if current_teacher_id is null then
    raise exception 'Authentication is required to import students.' using errcode = '42501';
  end if;

  create temporary table import_student_map(student_key text primary key, student_id uuid) on commit drop;

  for student_record in select value from jsonb_array_elements(coalesce(p_students, '[]'::jsonb)) loop
    if nullif(trim(student_record->>'name'), '') is null then
      raise exception 'Every student must have a name.' using errcode = '22023';
    end if;
    insert into public.students(teacher_id, first_name, last_name, name, initials, accent)
    values (
      current_teacher_id,
      nullif(trim(student_record->>'first_name'), ''),
      nullif(trim(student_record->>'last_name'), ''),
      trim(student_record->>'name'),
      upper(left(regexp_replace(trim(student_record->>'name'), '[^[:alnum:] ]', '', 'g'), 2)),
      'sage'
    ) returning id into created_student_id;
    insert into import_student_map(student_key, student_id) values (student_record->>'student_key', created_student_id);
    students_imported := students_imported + 1;
  end loop;

  for guardian_record in select value from jsonb_array_elements(coalesce(p_guardians, '[]'::jsonb)) loop
    select student_id into created_student_id from import_student_map where student_key = guardian_record->>'student_key';
    if created_student_id is null then
      raise exception 'Guardian references an unknown student.' using errcode = '22023';
    end if;
    if nullif(trim(guardian_record->>'name'), '') is null or nullif(trim(guardian_record->>'relationship'), '') is null then
      raise exception 'Every guardian must have a name and relationship.' using errcode = '22023';
    end if;
    insert into public.guardians(student_id, name, relation, phone, email, preferred_contact_method)
    values (created_student_id, trim(guardian_record->>'name'), trim(guardian_record->>'relationship'), nullif(trim(guardian_record->>'phone'), ''), nullif(trim(guardian_record->>'email'), ''), null);
    guardians_imported := guardians_imported + 1;
  end loop;

  return jsonb_build_object('students_imported', students_imported, 'guardians_imported', guardians_imported);
end;
$$;

revoke all on function public.import_students(jsonb, jsonb) from public, anon;
grant execute on function public.import_students(jsonb, jsonb) to authenticated;
