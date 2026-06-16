-- Statistical evaluation experiments and run comparisons.
-- These tables are backend/admin only and must only be accessed with service_role.

create table if not exists public.evaluation_experiments (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  dataset_id uuid not null references public.evaluation_datasets(id)
    on delete cascade,
  baseline_run_id uuid not null references public.evaluation_runs(id)
    on delete cascade,
  challenger_run_id uuid not null references public.evaluation_runs(id)
    on delete cascade,
  comparison_type text not null default 'auto'
    check (comparison_type in ('auto', 'continuous', 'binary', 'ordinal')),
  metric_name text not null default 'score',
  minimum_practical_effect numeric(12, 6) not null default 0.02
    check (minimum_practical_effect >= 0),
  alpha numeric(6, 5) not null default 0.05
    check (alpha > 0 and alpha < 1),
  correction_method text not null default 'none'
    check (correction_method in ('none', 'bonferroni', 'benjamini_hochberg')),
  status text not null default 'draft'
    check (status in ('draft', 'running', 'completed', 'failed')),
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  summary jsonb not null default '{}'::jsonb,
  constraint evaluation_experiments_summary_object
    check (jsonb_typeof(summary) = 'object'),
  constraint evaluation_experiments_distinct_runs
    check (baseline_run_id <> challenger_run_id)
);

create table if not exists public.evaluation_comparisons (
  id uuid primary key default gen_random_uuid(),
  experiment_id uuid not null references public.evaluation_experiments(id)
    on delete cascade,
  baseline_run_id uuid not null references public.evaluation_runs(id)
    on delete cascade,
  challenger_run_id uuid not null references public.evaluation_runs(id)
    on delete cascade,
  metric_name text not null,
  baseline_mean numeric(16, 8),
  challenger_mean numeric(16, 8),
  absolute_difference numeric(16, 8),
  relative_difference numeric(16, 8),
  confidence_interval_low numeric(16, 8),
  confidence_interval_high numeric(16, 8),
  p_value numeric(16, 12),
  effect_size numeric(16, 8),
  sample_size integer not null default 0 check (sample_size >= 0),
  statistical_significance boolean not null default false,
  practical_significance boolean not null default false,
  recommendation text not null default 'inconclusive',
  warnings jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  constraint evaluation_comparisons_warnings_array
    check (jsonb_typeof(warnings) = 'array')
);

comment on table public.evaluation_experiments is
  'Controlled admin-only experiments comparing baseline and challenger evaluation runs.';
comment on table public.evaluation_comparisons is
  'Statistical comparison results for evaluation experiments.';

create index if not exists evaluation_experiments_dataset_id_created_at_idx
  on public.evaluation_experiments (dataset_id, created_at desc);

create index if not exists evaluation_experiments_status_created_at_idx
  on public.evaluation_experiments (status, created_at desc);

create index if not exists evaluation_experiments_baseline_run_id_idx
  on public.evaluation_experiments (baseline_run_id);

create index if not exists evaluation_experiments_challenger_run_id_idx
  on public.evaluation_experiments (challenger_run_id);

create index if not exists evaluation_comparisons_experiment_id_created_at_idx
  on public.evaluation_comparisons (experiment_id, created_at desc);

create index if not exists evaluation_comparisons_runs_metric_idx
  on public.evaluation_comparisons (
    baseline_run_id,
    challenger_run_id,
    metric_name
  );

alter table public.evaluation_experiments enable row level security;
alter table public.evaluation_comparisons enable row level security;

revoke all on table public.evaluation_experiments from anon, authenticated;
revoke all on table public.evaluation_comparisons from anon, authenticated;

grant select, insert, update, delete on table public.evaluation_experiments
  to service_role;
grant select, insert, update, delete on table public.evaluation_comparisons
  to service_role;

drop policy if exists "service role can manage evaluation experiments"
  on public.evaluation_experiments;
create policy "service role can manage evaluation experiments"
  on public.evaluation_experiments
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role can manage evaluation comparisons"
  on public.evaluation_comparisons;
create policy "service role can manage evaluation comparisons"
  on public.evaluation_comparisons
  for all
  to service_role
  using (true)
  with check (true);
