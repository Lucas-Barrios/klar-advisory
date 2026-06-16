-- Base diagnostic schema required by later telemetry/evaluation migrations.
-- This migration is additive and idempotent for existing deployments.

create extension if not exists pgcrypto;

create table if not exists public.students (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  name text,
  full_name text,
  email text not null,
  country text not null,
  age integer,
  pathway text not null
    check (pathway in ('university', 'ausbildung', 'work_visa')),
  german_level text not null
    check (german_level in ('none', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
  english_level text,
  education_level text not null,
  field_of_study text,
  work_experience_years integer not null default 0
    check (work_experience_years >= 0),
  timeline text not null
    check (timeline in ('6_months', '1_year', '2_years_plus')),
  financial_situation text,
  current_location text,
  additional_info text,
  constraint students_name_or_full_name_present
    check (
      nullif(btrim(coalesce(name, '')), '') is not null
      or nullif(btrim(coalesce(full_name, '')), '') is not null
    )
);

alter table public.students
  add column if not exists name text,
  add column if not exists full_name text,
  add column if not exists email text,
  add column if not exists country text,
  add column if not exists age integer,
  add column if not exists pathway text,
  add column if not exists german_level text,
  add column if not exists english_level text,
  add column if not exists education_level text,
  add column if not exists field_of_study text,
  add column if not exists work_experience_years integer default 0,
  add column if not exists timeline text,
  add column if not exists financial_situation text,
  add column if not exists current_location text,
  add column if not exists additional_info text;

update public.students
set name = full_name
where name is null
  and full_name is not null;

update public.students
set full_name = name
where full_name is null
  and name is not null;

create table if not exists public.diagnostics (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  student_id uuid references public.students(id) on delete cascade,
  overall_score integer check (overall_score >= 0 and overall_score <= 100),
  language_score integer,
  education_score integer,
  pathway_fit_score integer,
  timeline_score integer,
  financial_score integer,
  documentation_score integer,
  summary text,
  roadmap jsonb not null default '[]'::jsonb,
  recommendations jsonb not null default '[]'::jsonb,
  raw_output text,
  status text not null default 'pending'
    check (status in ('pending', 'approved', 'rejected')),
  reviewed_at timestamptz,
  reviewer_notes text,
  completed_steps integer[] not null default '{}'::integer[],
  progress_token_hash text
);

alter table public.diagnostics
  add column if not exists student_id uuid references public.students(id) on delete cascade,
  add column if not exists overall_score integer,
  add column if not exists language_score integer,
  add column if not exists education_score integer,
  add column if not exists pathway_fit_score integer,
  add column if not exists timeline_score integer,
  add column if not exists financial_score integer,
  add column if not exists documentation_score integer,
  add column if not exists summary text,
  add column if not exists roadmap jsonb default '[]'::jsonb,
  add column if not exists recommendations jsonb default '[]'::jsonb,
  add column if not exists raw_output text,
  add column if not exists status text default 'pending',
  add column if not exists reviewed_at timestamptz,
  add column if not exists reviewer_notes text,
  add column if not exists completed_steps integer[] default '{}'::integer[],
  add column if not exists progress_token_hash text;

create table if not exists public.audit_log (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  diagnostic_id uuid references public.diagnostics(id) on delete set null,
  action text not null,
  actor text not null,
  details jsonb not null default '{}'::jsonb
);

alter table public.audit_log
  add column if not exists diagnostic_id uuid references public.diagnostics(id) on delete set null,
  add column if not exists action text,
  add column if not exists actor text,
  add column if not exists details jsonb default '{}'::jsonb;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'diagnostics_overall_score_range'
  ) then
    alter table public.diagnostics
      add constraint diagnostics_overall_score_range
      check (overall_score is null or overall_score between 0 and 100);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'diagnostics_status_allowed'
  ) then
    alter table public.diagnostics
      add constraint diagnostics_status_allowed
      check (status in ('pending', 'approved', 'rejected'));
  end if;
end $$;

comment on table public.students is
  'Student intake profiles. Canonical display name is name; full_name is retained as a compatibility alias.';
comment on column public.students.name is
  'Canonical student display name used by backend and frontend code.';
comment on column public.students.full_name is
  'Compatibility alias for older frontend/result code. Keep synchronized during migrations.';
comment on column public.diagnostics.progress_token_hash is
  'SHA-256 hash of the bearer token required for public progress updates.';
comment on table public.audit_log is
  'Operational audit log for diagnostic lifecycle and safe telemetry fallbacks.';

create index if not exists students_email_idx
  on public.students (email);

create index if not exists diagnostics_student_id_idx
  on public.diagnostics (student_id);

create index if not exists diagnostics_status_created_at_idx
  on public.diagnostics (status, created_at desc);

create index if not exists audit_log_diagnostic_id_created_at_idx
  on public.audit_log (diagnostic_id, created_at desc);

alter table public.students enable row level security;
alter table public.diagnostics enable row level security;
alter table public.audit_log enable row level security;

revoke all on table public.students from anon, authenticated;
revoke all on table public.diagnostics from anon, authenticated;
revoke all on table public.audit_log from anon, authenticated;

grant select, insert, update, delete on table public.students to service_role;
grant select, insert, update, delete on table public.diagnostics to service_role;
grant select, insert, update, delete on table public.audit_log to service_role;

drop policy if exists "service role can manage students"
  on public.students;
create policy "service role can manage students"
  on public.students
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role can manage diagnostics"
  on public.diagnostics;
create policy "service role can manage diagnostics"
  on public.diagnostics
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role can manage audit log"
  on public.audit_log;
create policy "service role can manage audit log"
  on public.audit_log
  for all
  to service_role
  using (true)
  with check (true);
