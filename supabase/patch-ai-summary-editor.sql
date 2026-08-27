-- Run once in Supabase SQL Editor for editable, versioned AI summaries.
create table if not exists public.ai_contact_briefs (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  date_from timestamptz not null,
  date_to timestamptz not null,
  version integer not null check (version > 0),
  status text not null default 'draft' check (status in ('draft', 'approved', 'superseded')),
  key_topics jsonb not null default '[]'::jsonb,
  parent_concerns jsonb not null default '[]'::jsonb,
  recorded_resolutions jsonb not null default '[]'::jsonb,
  open_items jsonb not null default '[]'::jsonb,
  suggested_next_step text,
  generated_at timestamptz not null default now(),
  approved_at timestamptz,
  updated_at timestamptz not null default now(),
  unique (student_id, date_from, date_to, version)
);

alter table public.ai_contact_briefs enable row level security;
drop policy if exists "demo read ai briefs" on public.ai_contact_briefs;
drop policy if exists "demo insert ai briefs" on public.ai_contact_briefs;
drop policy if exists "demo update ai briefs" on public.ai_contact_briefs;
drop policy if exists "demo delete ai briefs" on public.ai_contact_briefs;
create policy "demo read ai briefs" on public.ai_contact_briefs for select to anon using (true);
create policy "demo insert ai briefs" on public.ai_contact_briefs for insert to anon with check (true);
create policy "demo update ai briefs" on public.ai_contact_briefs for update to anon using (true) with check (true);
create policy "demo delete ai briefs" on public.ai_contact_briefs for delete to anon using (true);

create index if not exists ai_contact_briefs_latest_idx on public.ai_contact_briefs(student_id, date_from, date_to, version desc);
