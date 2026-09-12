-- ContactLoop FastAPI + Supabase compatibility migration.
-- Apply only after review, through the Supabase SQL Editor or a reviewed migration runner.
-- This script adds structures and access controls only. It does not remove rows,
-- tables, columns, or existing contact-history data.

create extension if not exists pgcrypto;

create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  email varchar(320) not null unique,
  name varchar(255),
  password_hash text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  created_by uuid,
  updated_by uuid,
  deleted_at timestamptz
);

create table if not exists public.auth_tokens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  token_hash varchar(64) not null unique,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  created_by uuid,
  updated_by uuid,
  deleted_at timestamptz
);

create index if not exists auth_tokens_user_id_idx on public.auth_tokens(user_id);

alter table public.students add column if not exists owner_id uuid references public.users(id) on delete set null;
alter table public.students add column if not exists first_name text;
alter table public.students add column if not exists last_name text;
alter table public.students add column if not exists updated_at timestamptz not null default now();
alter table public.students add column if not exists created_by uuid references public.users(id) on delete set null;
alter table public.students add column if not exists updated_by uuid references public.users(id) on delete set null;
alter table public.students add column if not exists deleted_at timestamptz;

alter table public.guardians add column if not exists email text;
alter table public.guardians add column if not exists preferred_contact_method text;
alter table public.guardians alter column phone drop not null;
alter table public.guardians add column if not exists updated_at timestamptz not null default now();
alter table public.guardians add column if not exists created_by uuid references public.users(id) on delete set null;
alter table public.guardians add column if not exists updated_by uuid references public.users(id) on delete set null;
alter table public.guardians add column if not exists deleted_at timestamptz;

alter table public.contact_events alter column guardian_id drop not null;
alter table public.contact_events add column if not exists updated_at timestamptz not null default now();
alter table public.contact_events add column if not exists created_by uuid references public.users(id) on delete set null;
alter table public.contact_events add column if not exists updated_by uuid references public.users(id) on delete set null;
alter table public.contact_events add column if not exists deleted_at timestamptz;

alter table public.follow_ups add column if not exists completed_at timestamptz;
alter table public.follow_ups add column if not exists updated_at timestamptz not null default now();
alter table public.follow_ups add column if not exists created_by uuid references public.users(id) on delete set null;
alter table public.follow_ups add column if not exists updated_by uuid references public.users(id) on delete set null;
alter table public.follow_ups add column if not exists deleted_at timestamptz;

alter table public.teacher_notes add column if not exists created_by uuid references public.users(id) on delete set null;
alter table public.teacher_notes add column if not exists updated_by uuid references public.users(id) on delete set null;
alter table public.teacher_notes add column if not exists deleted_at timestamptz;

alter table public.ai_contact_briefs add column if not exists created_at timestamptz not null default now();
alter table public.ai_contact_briefs add column if not exists created_by uuid references public.users(id) on delete set null;
alter table public.ai_contact_briefs add column if not exists updated_by uuid references public.users(id) on delete set null;
alter table public.ai_contact_briefs add column if not exists deleted_at timestamptz;

create index if not exists students_owner_name_alive_idx
  on public.students(owner_id, name)
  where deleted_at is null;
create index if not exists guardians_student_alive_idx
  on public.guardians(student_id)
  where deleted_at is null;
create index if not exists contact_events_student_call_alive_idx
  on public.contact_events(student_id, call_time)
  where deleted_at is null;
create index if not exists follow_ups_student_due_alive_idx
  on public.follow_ups(student_id, due_at)
  where deleted_at is null;
create index if not exists teacher_notes_student_created_alive_idx
  on public.teacher_notes(student_id, created_at)
  where deleted_at is null;
create index if not exists ai_contact_briefs_student_range_alive_idx
  on public.ai_contact_briefs(student_id, date_from, date_to, version desc)
  where deleted_at is null;

-- Server-side binding of voice-note upload object keys to their owner.
create table if not exists public.voice_note_objects (
  id uuid primary key default gen_random_uuid(),
  object_key varchar(64) not null unique,
  student_id uuid not null references public.students(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  created_by uuid,
  updated_by uuid,
  deleted_at timestamptz
);

create index if not exists voice_note_objects_user_idx on public.voice_note_objects(user_id);
create index if not exists voice_note_objects_student_idx on public.voice_note_objects(student_id);

-- Browser clients no longer access these tables directly. FastAPI owns
-- authentication and authorization, while the existing Agent continues to use
-- its server-side service-role credentials.
alter table public.users enable row level security;
alter table public.auth_tokens enable row level security;
alter table public.students enable row level security;
alter table public.guardians enable row level security;
alter table public.contact_events enable row level security;
alter table public.follow_ups enable row level security;
alter table public.teacher_notes enable row level security;
alter table public.ai_contact_briefs enable row level security;
alter table public.voice_note_objects enable row level security;

do $$
declare
  existing_policy record;
begin
  for existing_policy in
    select schemaname, tablename, policyname
    from pg_policies
    where schemaname = 'public'
      and tablename in (
        'users',
        'auth_tokens',
        'students',
        'guardians',
        'contact_events',
        'follow_ups',
        'teacher_notes',
        'ai_contact_briefs',
        'voice_note_objects'
      )
  loop
    execute format(
      'drop policy if exists %I on %I.%I',
      existing_policy.policyname,
      existing_policy.schemaname,
      existing_policy.tablename
    );
  end loop;
end;
$$;

-- `contact_events.discussed_topics` remains the existing text[] column.
-- FastAPI must use a PostgreSQL array variant for that field; this avoids a
-- destructive type conversion and keeps existing Agent responses unchanged.
