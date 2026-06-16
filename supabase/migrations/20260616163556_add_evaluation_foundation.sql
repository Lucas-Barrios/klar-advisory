-- Evaluation foundation for benchmark datasets, human-reviewed examples,
-- evaluation runs, and proposal-ready reporting metrics.
-- Evaluation rows should not store names, emails, raw prompts, or raw AI output.

alter table public.diagnostics
  add column if not exists diagnostic_prompt_version text not null
    default 'germany_diagnostic_prompt_v1',
  add column if not exists diagnostic_rubric_version text not null
    default 'germany_readiness_rubric_v1',
  add column if not exists reviewer_decision text,
  add column if not exists reviewer_correction_notes text,
  add column if not exists reviewer_confidence integer,
  add column if not exists rejection_reason text,
  add column if not exists review_duration_seconds integer;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'diagnostics_reviewer_confidence_range'
  ) then
    alter table public.diagnostics
      add constraint diagnostics_reviewer_confidence_range
      check (
        reviewer_confidence is null
        or reviewer_confidence between 1 and 5
      );
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'diagnostics_review_duration_nonnegative'
  ) then
    alter table public.diagnostics
      add constraint diagnostics_review_duration_nonnegative
      check (
        review_duration_seconds is null
        or review_duration_seconds >= 0
      );
  end if;
end $$;

create table if not exists public.evaluation_datasets (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  version text not null,
  use_case text not null,
  description text,
  created_at timestamptz not null default now(),
  active boolean not null default true,
  constraint evaluation_datasets_name_version_use_case_unique
    unique (name, version, use_case)
);

create table if not exists public.evaluation_examples (
  id uuid primary key default gen_random_uuid(),
  dataset_id uuid not null references public.evaluation_datasets(id)
    on delete cascade,
  input_payload jsonb not null default '{}'::jsonb,
  expected_pathway text,
  expected_german_level text,
  expected_timeline text,
  expected_flags jsonb not null default '[]'::jsonb,
  expected_summary_notes text,
  source text,
  reviewed_by_human boolean not null default false,
  created_at timestamptz not null default now(),
  constraint evaluation_examples_expected_flags_array
    check (jsonb_typeof(expected_flags) = 'array'),
  constraint evaluation_examples_input_payload_no_direct_pii_keys
    check (
      not (
        input_payload ?| array[
          'email',
          'student_email',
          'raw_output',
          'prompt',
          'raw_prompt',
          'additional_info'
        ]
      )
    )
);

create table if not exists public.evaluation_runs (
  id uuid primary key default gen_random_uuid(),
  dataset_id uuid not null references public.evaluation_datasets(id)
    on delete cascade,
  model text not null,
  prompt_version text not null,
  rubric_version text not null,
  run_type text not null default 'manual',
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  status text not null default 'running'
    check (status in ('running', 'completed', 'failed')),
  summary_metrics jsonb not null default '{}'::jsonb,
  constraint evaluation_runs_summary_metrics_object
    check (jsonb_typeof(summary_metrics) = 'object')
);

create table if not exists public.evaluation_results (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.evaluation_runs(id) on delete cascade,
  example_id uuid not null references public.evaluation_examples(id)
    on delete cascade,
  diagnostic_id uuid references public.diagnostics(id) on delete set null,
  model text,
  prompt_version text,
  rubric_version text,
  predicted_pathway text,
  predicted_german_level text,
  predicted_timeline text,
  predicted_flags jsonb not null default '[]'::jsonb,
  score numeric(5, 4) not null default 0 check (score >= 0 and score <= 1),
  passed boolean not null default false,
  error_type text,
  latency_ms integer not null default 0 check (latency_ms >= 0),
  input_tokens integer not null default 0 check (input_tokens >= 0),
  output_tokens integer not null default 0 check (output_tokens >= 0),
  estimated_cost numeric(12, 8) not null default 0 check (estimated_cost >= 0),
  notes text,
  created_at timestamptz not null default now(),
  constraint evaluation_results_predicted_flags_array
    check (jsonb_typeof(predicted_flags) = 'array')
);

comment on table public.evaluation_datasets is
  'Benchmark dataset metadata for diagnostic AI evaluation.';
comment on table public.evaluation_examples is
  'Sanitized benchmark examples. Excludes direct PII such as names and emails.';
comment on table public.evaluation_runs is
  'Evaluation run metadata with prompt/rubric version tracking.';
comment on table public.evaluation_results is
  'Per-example evaluation outcomes, telemetry, and scoring.';

create index if not exists evaluation_datasets_active_created_at_idx
  on public.evaluation_datasets (active, created_at desc);

create index if not exists evaluation_examples_dataset_id_created_at_idx
  on public.evaluation_examples (dataset_id, created_at desc);

create index if not exists evaluation_runs_dataset_id_started_at_idx
  on public.evaluation_runs (dataset_id, started_at desc);

create index if not exists evaluation_runs_status_started_at_idx
  on public.evaluation_runs (status, started_at desc);

create index if not exists evaluation_results_run_id_created_at_idx
  on public.evaluation_results (run_id, created_at desc);

create index if not exists evaluation_results_example_id_idx
  on public.evaluation_results (example_id);

alter table public.evaluation_datasets enable row level security;
alter table public.evaluation_examples enable row level security;
alter table public.evaluation_runs enable row level security;
alter table public.evaluation_results enable row level security;

revoke all on table public.evaluation_datasets from anon, authenticated;
revoke all on table public.evaluation_examples from anon, authenticated;
revoke all on table public.evaluation_runs from anon, authenticated;
revoke all on table public.evaluation_results from anon, authenticated;

grant select, insert, update, delete on table public.evaluation_datasets
  to service_role;
grant select, insert, update, delete on table public.evaluation_examples
  to service_role;
grant select, insert, update, delete on table public.evaluation_runs
  to service_role;
grant select, insert, update, delete on table public.evaluation_results
  to service_role;

drop policy if exists "service role can manage evaluation datasets"
  on public.evaluation_datasets;
create policy "service role can manage evaluation datasets"
  on public.evaluation_datasets
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role can manage evaluation examples"
  on public.evaluation_examples;
create policy "service role can manage evaluation examples"
  on public.evaluation_examples
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role can manage evaluation runs"
  on public.evaluation_runs;
create policy "service role can manage evaluation runs"
  on public.evaluation_runs
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role can manage evaluation results"
  on public.evaluation_results;
create policy "service role can manage evaluation results"
  on public.evaluation_results
  for all
  to service_role
  using (true)
  with check (true);
