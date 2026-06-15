# MVP Documentation
## Klar — Germany Readiness Diagnostic Platform
### Ironhack Berlin AI & Integration Consulting · June 2026

---

## 1. What Was Built

Klar is a full-stack AI-powered product that delivers personalised Germany readiness diagnostics to Latin American students and professionals. It was built in 5 days as the MVP for the Ironhack Berlin AI & Integration Consulting capstone project.

**Live URL:** https://klar-advisory.vercel.app
**GitHub:** https://github.com/Lucas-Barrios/klar-advisory
**API Docs:** https://klar-backend.onrender.com/docs

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────┐
│                   KLAR MVP                      │
├──────────────────┬──────────────────────────────┤
│   FRONTEND       │   BACKEND                    │
│   Next.js 15     │   FastAPI (Python)            │
│   TypeScript     │   LangChain                  │
│   Tailwind CSS   │   Anthropic Claude Sonnet    │
│   Supabase JS    │   Supabase Python SDK        │
│   Vercel         │   Render                     │
└──────────────────┴──────────────────────────────┘
                    │
                    ▼
            SUPABASE (PostgreSQL)
            EU Region — Frankfurt
                    │
                    ▼
              n8n (planned)
           Email notifications
```

---

## 3. File Structure

```
klar-advisory/
├── frontend/                    # Next.js 15 app
│   ├── app/
│   │   ├── page.tsx            # Landing page
│   │   ├── diagnostic/
│   │   │   └── page.tsx        # Conversational intake form
│   │   ├── results/
│   │   │   ├── [id]/
│   │   │   │   ├── page.tsx    # Results page (pending/approved)
│   │   │   │   └── CopyLinkButton.tsx
│   │   │   └── demo/
│   │   │       └── page.tsx    # Demo results (static)
│   │   ├── admin/
│   │   │   └── page.tsx        # Consultant dashboard
│   │   ├── layout.tsx          # Root layout + nav
│   │   ├── globals.css         # Design system + animations
│   │   ├── not-found.tsx       # 404 page
│   │   └── error.tsx           # Error boundary
│   ├── lib/
│   │   └── supabase.ts         # Supabase client
│   ├── .env.local              # Environment variables (not committed)
│   └── package.json
│
├── backend/                     # FastAPI Python app
│   ├── main.py                 # App entry point + CORS
│   ├── database.py             # Supabase client
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── agents/
│   │   └── germany_diagnostic.py  # LangChain + Claude agent
│   ├── routers/
│   │   ├── diagnostic.py       # POST /api/diagnostic/
│   │   └── admin.py            # GET/POST /api/admin/*
│   ├── requirements.txt
│   └── .env                    # Environment variables (not committed)
│
└── n8n/                        # Notification workflows (planned)
    └── klar_notifications.json
```

---

## 4. Core AI Component — Germany Diagnostic Agent

The diagnostic agent is the heart of the product. It is implemented in `backend/agents/germany_diagnostic.py`.

### How It Works

**Input:** Student profile dictionary (13 fields from the intake form)

**Model:** Anthropic Claude Sonnet (`claude-sonnet-4-6`)

**Temperature:** 0.3 (low — reduces variability in scoring)

**Output format:** JSON with explicit structure enforcement in the system prompt

**Processing steps:**
1. Student profile is formatted into a structured user message
2. System prompt provides the full scoring rubric with numeric anchors
3. Claude generates a JSON response with scores, summary, roadmap, and recommendations
4. Response is parsed and validated
5. Stored in Supabase with status `pending`
6. n8n webhook fires to notify consultant (when configured)

### Scoring Rubric

| Dimension | Weight | Anchor Values |
|---|---|---|
| Language Score | 25% | none=10, A1=20, A2=35, B1=55, B2=75, C1=90, C2=100 |
| Education Score | 20% | Based on degree level, field relevance, recognition likelihood |
| Pathway Fit Score | 20% | Depends on pathway — Ausbildung needs B1+, University needs B2+ |
| Timeline Score | 15% | 6 months=tight(20–40), 1 year=realistic(50–70), 2+ years=ideal(70–90) |
| Financial Score | 10% | University needs ~€11,000 blocked account; Ausbildung pays salary |
| Documentation Score | 10% | EU=easy, LATAM with degree=moderate, without=complex |

**Overall score:** Weighted average of all 6 dimensions

**Score interpretation:**
- Below 40: Not ready yet
- 40–60: Getting there
- 60–80: Ready with preparation
- 80+: Strong candidate

---

## 5. API Endpoints

**Base URL:** `https://klar-backend.onrender.com`
**Interactive docs:** `https://klar-backend.onrender.com/docs`

### POST /api/diagnostic/
Submit a new student diagnostic.

**Request body:**
```json
{
  "name": "Maria García",
  "email": "maria@example.com",
  "country": "Colombia",
  "age": 26,
  "pathway": "ausbildung",
  "german_level": "A2",
  "english_level": "B2",
  "education_level": "bachelor",
  "field_of_study": "Nursing",
  "work_experience_years": 2,
  "timeline": "1_year",
  "financial_situation": "I have some savings but need funded options",
  "current_location": "Bogotá",
  "additional_info": ""
}
```

**Response:**
```json
{
  "diagnostic_id": "3833b45e-f063-4137-88d1-8d86ab93bd5e",
  "status": "pending",
  "message": "Your diagnostic is being reviewed. You will receive your results by email once approved."
}
```

**What happens internally:**
1. Student saved to `students` table
2. Agent runs — Claude generates scores, roadmap, recommendations
3. Diagnostic saved to `diagnostics` table with `status: pending`
4. Audit log entry created
5. n8n webhook fired (if configured)

---

### GET /api/admin/diagnostics
Returns all pending diagnostics with nested student data.

**Auth:** No token auth at MVP — admin dashboard is password-protected client-side.

**Response:** Array of diagnostic objects with nested `students` object.

---

### GET /api/admin/diagnostics/{id}
Returns a single diagnostic by ID with full student data.

---

### POST /api/admin/diagnostics/{id}/review
Approve or reject a diagnostic.

**Request body:**
```json
{
  "status": "approved",
  "reviewer_notes": "Strong nursing background. Roadmap is realistic. Approved."
}
```

**What happens:**
1. Diagnostic status updated in Supabase
2. `reviewed_at` timestamp set
3. Audit log entry created (`review_approved` or `review_rejected`)
4. (Planned) n8n webhook fires to send approval email to student

---

### GET /api/admin/stats
Returns platform statistics.

**Response:**
```json
{
  "pending": 3,
  "approved_today": 7,
  "total": 24
}
```

---

### GET /health
Health check endpoint.

**Response:** `{"status": "ok", "product": "Klar"}`

---

## 6. Database Schema

```sql
-- Students table
CREATE TABLE students (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  country TEXT NOT NULL,
  age INTEGER,
  pathway TEXT NOT NULL,
  german_level TEXT NOT NULL,
  english_level TEXT,
  education_level TEXT NOT NULL,
  field_of_study TEXT,
  work_experience_years INTEGER DEFAULT 0,
  timeline TEXT NOT NULL,
  financial_situation TEXT,
  current_location TEXT,
  additional_info TEXT
);

-- Diagnostics table
CREATE TABLE diagnostics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  student_id UUID REFERENCES students(id) ON DELETE CASCADE,
  overall_score INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
  language_score INTEGER,
  education_score INTEGER,
  pathway_fit_score INTEGER,
  timeline_score INTEGER,
  financial_score INTEGER,
  documentation_score INTEGER,
  summary TEXT,
  roadmap JSONB,
  recommendations JSONB,
  raw_output TEXT,
  status TEXT DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved', 'rejected')),
  reviewed_at TIMESTAMPTZ,
  reviewer_notes TEXT
);

-- Audit log (EU AI Act Article 12)
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  diagnostic_id UUID REFERENCES diagnostics(id),
  action TEXT NOT NULL,
  actor TEXT NOT NULL,
  details JSONB
);
```

---

## 7. Frontend Pages

### / — Landing Page
Dark hero with gradient headline, stats bar, numbered feature cards. CTA to start diagnostic and link to demo result.

### /diagnostic — Conversational Intake Form
11 questions, one per screen. Slide animation between questions. Auto-advance on choice selection. Full-screen loading state with cycling messages during API call.

### /results/[id] — Results Page
Two states:
- **Pending:** Checkmark icon, "being reviewed" message, copy link button
- **Approved:** Circular score gauge, 6 dimension bars with fill animation, vertical timeline roadmap, 3 recommendation cards, share/CTA footer

### /results/demo — Demo Results
Static pre-populated results for Carlos Mendoza (68/100 score). Amber demo banner at top. Identical layout to approved results.

### /admin — Consultant Dashboard
Password gate (klar2026). Time-aware greeting. Real stats from API. Diagnostic cards with score bars and pathway badges. Filter tabs by pathway. Slide-in details panel with full diagnostic, notes textarea, approve/reject buttons. Toast notifications.

---

## 8. Design System

| Token | Value | Usage |
|---|---|---|
| `--bg` | `#0A0E1A` | Main background |
| `--bg2` | `#111827` | Card backgrounds |
| `--blue` | `#3B82F6` | Primary accent |
| `--purple` | `#8B5CF6` | Gradient partner |
| `--teal` | `#0D9488` | Success/positive |
| `--amber` | `#F59E0B` | Warnings/medium |
| `--red` | `#EF4444` | Errors/low scores |
| `--text` | `#F9FAFB` | Primary text |
| `--text2` | `#9CA3AF` | Secondary text |
| Font | Space Grotesk | All text |

**Key CSS utilities:**
- `.gradient-text` — blue-to-purple gradient text
- `.glass` — frosted glass card effect
- `.glow-blue` — blue ambient glow
- `.animate-fade-up` — staggered entrance animation
- `fillBar` keyframe — animated progress bar fill

---

## 9. Running Locally

**Prerequisites:** Node.js 18+, Python 3.11+, Supabase account, Anthropic API key

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env with ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
venv/bin/uvicorn main:app --reload
# Runs on http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm install
# Create .env.local with NEXT_PUBLIC_SUPABASE_URL, 
# NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL
npm run dev
# Runs on http://localhost:3001
```

---

## 10. What a Developer Would Need to Continue Building

**Next use cases to implement:**
- UC-02 Ausbildung Position Matcher — RAG pipeline with DAAD course data
- UC-04 Document Factory — AI-generated German CV and cover letter
- UC-05 Lead Nurturing — n8n workflow for follow-up sequences

**Technical improvements for scale:**
- Add JWT authentication to admin routes (replace password gate)
- Implement n8n email notification workflow
- Add rate limiting on the diagnostic endpoint (prevent abuse)
- Switch to smaller model (claude-haiku-4-5) for cost efficiency at scale
- Add Giskard bias testing pipeline to CI/CD
- Implement Spanish language version of the frontend
- Add Stripe payment integration for paid tiers

**Infrastructure for scale:**
- Upgrade Supabase to Pro plan (connection pooling)
- Add Redis caching for repeated similar profiles
- Add a queue (e.g. BullMQ) for diagnostic processing to handle spikes
- Implement webhook retry logic for n8n failures

---

*MVP Documentation · Klar · Ironhack Berlin AI & Integration Consulting · June 2026*
