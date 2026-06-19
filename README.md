# Klar — Germany Readiness Diagnostic & Application Platform

> Clear answers. Real pathways.

---

## What it is

Klar is an AI-powered platform helping Latin American students and professionals assess Germany readiness across university, Ausbildung, and work visa pathways. A student completes an 11-question intake form; Claude Sonnet scores six weighted dimensions and generates a personalised readiness score and roadmap. Every result is reviewed and approved by a human consultant before being delivered — satisfying EU AI Act Article 14 mandatory human oversight. Students who want to act on their results can purchase a self-serve €39 Germany Application Kit that unlocks real Bundesagentur für Arbeit matched positions plus bilingual AI-generated CV and cover letter.

---

## Live

- **Frontend:** https://klar-advisory.vercel.app
- **Backend API:** https://klar-backend-ko6m.onrender.com

---

## How it works

1. Student completes an 11-question conversational intake form (language level, education, pathway goal, timeline, finances)
2. Claude Sonnet (`claude-sonnet-4-6`) scores six weighted dimensions — Language (25%), Education (20%), Pathway Fit (20%), Timeline (15%), Financial (10%), Documentation (10%) — and generates an overall readiness score (0–100), dimension breakdown, month-by-month roadmap, and three specific recommendations
3. Result stored as `pending` in Supabase; n8n webhook fires a "new diagnostic pending review" notification to Cleo
4. Cleo reviews the diagnostic in the admin dashboard and approves or returns for revision — no result reaches a student without human sign-off (EU AI Act Article 14)
5. On approval: Resend (via REST API) delivers a personalised result email to the student; the results page shows the full score and roadmap
6. Student can optionally purchase the **€39 Germany Application Kit** via Stripe Checkout — unlocks real Bundesagentur für Arbeit matched Ausbildung and job positions, plus bilingual (German + English/Spanish) AI-generated CV and cover letter with editable placeholders
7. A free 15-minute consultation (Cal.com) is available as an optional trust-building touchpoint

---

## Tech stack

**Backend (Python)**
- FastAPI 0.137.0
- Anthropic SDK 0.109.1 — raw SDK, not LangChain; wrapped with LangSmith 0.8.16 for tracing via EU endpoint (`eu.api.smith.langchain.com`)
- Supabase Python SDK 2.31.0 (PostgreSQL, EU-Frankfurt region)
- Stripe 15.2.1 (Checkout session creation + webhook signature verification)
- slowapi 0.1.9 (rate limiting)
- httpx 0.28.1 (Resend transactional email via REST API)
- uvicorn 0.49.0

**Frontend (TypeScript)**
- Next.js 16.2.9 (App Router)
- React 19
- Tailwind CSS v4
- @supabase/supabase-js 2.x
- lucide-react (icons)
- jspdf (client-side PDF export)

**Infrastructure**
- Vercel (frontend hosting)
- Render (backend hosting)
- Supabase (PostgreSQL, EU-Frankfurt)
- n8n (internal consultant notification only — "new diagnostic pending review" alert to Cleo; student-facing emails go through Resend directly, not n8n)
- LangSmith (AI tracing, EU endpoint)

---

## Project structure

```
klar-advisory/
├── backend/                        # FastAPI app
│   ├── main.py
│   ├── database.py
│   ├── agents/                     # AI agents (raw Anthropic SDK + LangSmith)
│   │   ├── germany_diagnostic.py
│   │   ├── ausbildung_matcher.py
│   │   └── document_factory.py
│   ├── routers/                    # API route handlers
│   │   ├── diagnostic.py
│   │   ├── admin.py
│   │   └── payments.py
│   ├── services/                   # Business logic
│   ├── models/                     # Pydantic schemas
│   ├── tests/                      # pytest suite (132 passing, 6 skipped)
│   └── requirements.txt
├── frontend/                       # Next.js App Router
│   └── app/
│       ├── page.tsx                # Landing page
│       ├── diagnostic/             # Conversational intake form
│       ├── results/[id]/           # Results page + Application Kit unlock
│       └── admin/                  # Consultant review dashboard
├── supabase/
│   └── migrations/                 # SQL migration files
├── docs/                           # Compliance, ROI, and strategic docs
└── final-project-lucas-barrios/    # Ironhack capstone submission copies
```

---

## Running locally

**Backend**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your real values
uvicorn main:app --reload
# Runs on http://localhost:8000
```

Required environment variables (see [backend/.env.example](backend/.env.example)):
`ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ADMIN_API_TOKEN`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `LANGSMITH_API_KEY`

**Frontend**

```bash
cd frontend
npm install
# Create .env.local with NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL
npm run dev
# Runs on http://localhost:3000
```

---

## Compliance

UC-01 (Germany Readiness Diagnostic) is classified High Risk under EU AI Act Annex III. Mandatory human oversight is implemented via the consultant review gate — no automated decision reaches a student without Cleo's sign-off (Article 14 satisfied). A GDPR Data Protection Impact Assessment has been completed. Full compliance documentation is in [docs/](docs/): conformity assessment, technical documentation outline, DPIA, and data flows.

---

## Testing

```bash
cd backend && pytest tests/ -v
```

132 passed, 6 skipped (June 2026).

---

## Author

Lucas Barrios — Ironhack Berlin, AI & Integration Consulting capstone, June 2026.
