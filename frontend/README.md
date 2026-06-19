# Klar — Frontend

Next.js 15 (App Router) frontend for the Klar Germany readiness diagnostic platform.

For full project context — architecture, backend setup, environment variables, deployment — see the [root README](../README.md).

## What this is

The Klar UI is a TypeScript/Tailwind CSS application built on the Next.js 15 App Router. It provides:

- A conversational 11-question intake form (`/diagnostic`)
- A results page that renders pending/approved diagnostics (`/results/[id]`)
- A static demo result for presentations (`/results/demo`)
- A consultant admin dashboard (`/admin`)

## Running locally

**Prerequisites:** Node.js 18+, a running backend (see `backend/`), a Supabase project.

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Fill in:
#   NEXT_PUBLIC_SUPABASE_URL
#   NEXT_PUBLIC_SUPABASE_ANON_KEY
#   NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# App runs on http://localhost:3001
```

See [`.env.local.example`](.env.local.example) for the full list of required variables.
