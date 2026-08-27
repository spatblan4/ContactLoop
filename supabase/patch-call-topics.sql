-- Separate why a call was made from what was actually discussed.
alter table public.contact_events add column if not exists planned_topic text;
alter table public.contact_events add column if not exists discussed_topics text[] not null default '{}';

create index if not exists contact_events_planned_topic_idx on public.contact_events(planned_topic);
create index if not exists contact_events_discussed_topics_idx on public.contact_events using gin(discussed_topics);
