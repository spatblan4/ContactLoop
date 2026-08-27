-- Run this once if schema.sql was already run before Add Student was added.
drop policy if exists "demo insert students" on public.students;
drop policy if exists "demo insert guardians" on public.guardians;
create policy "demo insert students" on public.students for insert to anon with check (true);
create policy "demo insert guardians" on public.guardians for insert to anon with check (true);
