alter table public.contact_events add column if not exists provider text not null default 'mock';
alter table public.contact_events add column if not exists provider_call_id text;
alter table public.contact_events add column if not exists provider_status text;
alter table public.contact_events add column if not exists started_at timestamptz;
alter table public.contact_events add column if not exists ended_at timestamptz;

alter table public.contact_events drop constraint if exists contact_events_result_check;
alter table public.contact_events add constraint contact_events_result_check check (result in ('Initiated', 'Ringing', 'Connected', 'No Answer', 'Busy', 'Failed'));

create unique index if not exists contact_events_provider_call_id_idx on public.contact_events(provider_call_id) where provider_call_id is not null;
