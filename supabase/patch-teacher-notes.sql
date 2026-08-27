-- Run once in Supabase SQL Editor for teacher-confirmed voice notes.
create table if not exists public.teacher_notes (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  contact_event_id uuid references public.contact_events(id) on delete set null,
  content text not null check (length(trim(content)) > 0),
  source text not null default 'typed' check (source in ('typed', 'voice')),
  teacher_confirmed boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.teacher_notes enable row level security;
drop policy if exists "demo read teacher notes" on public.teacher_notes;
drop policy if exists "demo insert teacher notes" on public.teacher_notes;
drop policy if exists "demo update teacher notes" on public.teacher_notes;
create policy "demo read teacher notes" on public.teacher_notes for select to anon using (true);
create policy "demo insert teacher notes" on public.teacher_notes for insert to anon with check (teacher_confirmed = true);
create policy "demo update teacher notes" on public.teacher_notes for update to anon using (true) with check (teacher_confirmed = true);

create index if not exists teacher_notes_student_created_idx on public.teacher_notes(student_id, created_at desc);
