-- AI usage telemetry for TCO observability.
-- Safe telemetry only: do not store raw prompts, names, emails, full profiles,
-- or personal diagnostic answers in this table.

create table if not exists public.ai_usage_events (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  provider text not null,
  model text not null,
  request_type text not null,
  diagnostic_id uuid references public.diagnostics(id) on delete set null,
  student_id uuid references public.students(id) on delete set null,
  input_tokens integer not null default 0 check (input_tokens >= 0),
  output_tokens integer not null default 0 check (output_tokens >= 0),
  total_tokens integer not null default 0 check (total_tokens >= 0),
  estimated_cost numeric(12, 8) not null default 0 check (estimated_cost >= 0),
  latency_ms integer not null default 0 check (latency_ms >= 0),
  success boolean not null,
  error_type text,
  details jsonb not null default '{}'::jsonb,
  constraint ai_usage_events_total_tokens_matches check (
    total_tokens = input_tokens + output_tokens
  ),
  constraint ai_usage_events_details_no_pii_keys check (
    not (
      details ?| array[
        'prompt',
        'raw_prompt',
        'student_name',
        'student_email',
        'email',
        'name',
        'profile',
        'answers',
        'full_profile',
        'raw_output'
      ]
    )
  )
);

comment on table public.ai_usage_events is
  'Safe AI usage telemetry for cost observability. Excludes raw prompts and PII.';

create index if not exists ai_usage_events_created_at_idx
  on public.ai_usage_events (created_at desc);

create index if not exists ai_usage_events_model_created_at_idx
  on public.ai_usage_events (model, created_at desc);

create index if not exists ai_usage_events_success_created_at_idx
  on public.ai_usage_events (success, created_at desc);

create index if not exists ai_usage_events_diagnostic_id_idx
  on public.ai_usage_events (diagnostic_id);

alter table public.ai_usage_events enable row level security;

revoke all on table public.ai_usage_events from anon, authenticated;
grant select, insert on table public.ai_usage_events to service_role;

drop policy if exists "service role can manage ai usage events"
  on public.ai_usage_events;

create policy "service role can manage ai usage events"
  on public.ai_usage_events
  for all
  to service_role
  using (true)
  with check (true);
