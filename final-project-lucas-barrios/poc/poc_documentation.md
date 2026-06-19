# POC Documentation
## Klar — Germany Readiness Diagnostic Agent
### Ironhack Berlin AI & Integration Consulting · June 2026

---

## A Note on Scope

This project consolidates the POC and MVP deliverables into a single working product rather than building a separate no-code prototype alongside it. Given the time available, building a full-stack, production-hardened application — complete with human-in-the-loop review, EU AI Act and GDPR compliance work, and a live audit trail — demonstrated more about real-world AI deployment than a parallel no-code workflow would have. The sections below describe this working system as the proof of concept: what AI capability it demonstrates, what a production version would add beyond it, and how to reproduce it.

---

## Demo Recording

**Live demo available at:** https://klar-advisory.vercel.app

**[VIDEO LINK PLACEHOLDER — Lucas to insert the actual hosted link here before final submission, e.g. Loom or YouTube unlisted URL]**

**What the recording should show:**
1. Student fills the conversational intake form (11 questions, ~3 minutes)
2. Loading screen with cycling AI messages
3. Pending screen showing student email and diagnostic ID
4. Admin dashboard — consultant reviews and approves
5. Student refreshes results page — full score, roadmap, recommendations visible

---

## 1. Tools Used and Why

| Tool | Role | Why chosen |
|---|---|---|
| FastAPI (Python) | Backend API | Fast to build, automatic Swagger docs, native async, Python AI ecosystem |
| Anthropic SDK (raw) | LLM calls to Claude Sonnet/Haiku | Direct SDK — no framework abstraction, traced via LangSmith |
| LangSmith | Observability and tracing | Wraps the Anthropic client via `wrap_anthropic`; captures every LLM call in the LangSmith UI |
| Anthropic Claude Sonnet | LLM for diagnostic generation | Best-in-class instruction following, structured JSON output, low hallucination rate |
| Supabase | Database and storage | PostgreSQL with Row Level Security, EU-region available for GDPR |
| Next.js 15 | Frontend | TypeScript, server components, file-based routing |
| n8n | Internal notification | Sends a webhook to alert the consultant when a new diagnostic needs review; student-facing emails (approval, payment confirmation) go through Resend directly |
| Vercel | Frontend deployment | Zero-config Next.js, global CDN |
| Render | Backend deployment | FastAPI-compatible, simple env var management |

---

## 2. What the POC Does — Step by Step

**Step 1 — Student submits profile**
Student visits the app and fills an 11-question conversational form (one question per screen, slide animation between questions). Questions cover: name, email, country, pathway, German level, English level, education, field of study, work experience, timeline, financial situation.

**Step 2 — API receives and validates the profile**
Frontend POSTs to `/api/diagnostic/`. FastAPI validates against the Pydantic schema. Malformed requests are rejected before reaching the AI agent.

**Step 3 — AI agent runs**
The validated profile is sent directly to Claude Sonnet via the raw Anthropic Python SDK (no LangChain). The system prompt contains the full scoring rubric with numeric anchors. Claude returns a JSON object with: overall score (0–100), 6 dimension scores, a 2–3 sentence summary, a month-by-month roadmap, and 3 specific recommendations. Every call is automatically traced to LangSmith via `wrap_anthropic`.

**Step 4 — Results saved to Supabase**
Student profile saved to `students` table. AI output saved to `diagnostics` table with `status: pending`. Audit log entry created (EU AI Act Article 12 compliance).

**Step 5 — Student sees pending screen**
API returns the `diagnostic_id`. Frontend redirects to `/results/[id]` showing a confirmation screen with the student's email.

**Step 6 — Consultant reviews in admin dashboard**
Cleo opens `/admin`, enters password. Dashboard loads pending diagnostics from the backend API. Each card shows student info, pathway badge, score bar. Cleo clicks "View details" to see full scores, summary, roadmap, and notes field.

**Step 7 — Consultant approves**
Cleo clicks "Approve." Backend updates status to `approved`, sets `reviewed_at`, logs the action.

**Step 8 — Student sees full results**
Student refreshes results page. Supabase returns `status: approved`. Full results render: animated circular score gauge, 6 dimension bars, summary with name, vertical timeline roadmap, 3 recommendation cards.

---

## 3. What AI Capability Is Demonstrated

**AI type:** Generative AI with agentic structured reasoning

Three capabilities demonstrated:

**Structured multi-dimensional assessment:** The agent applies a scoring rubric across 6 dimensions simultaneously, weighing each according to its importance for the chosen pathway. This is not retrieval — it is contextual reasoning and generation.

**Personalised roadmap generation:** The month-by-month roadmap adapts to the specific combination of pathway, language level, timeline, and financial situation. A B1-German nursing student with a 1-year timeline receives a materially different roadmap than an A2-German IT professional with 2 years.

**Constrained output for safety and compliance:** The agent generates structured JSON, not free text. This enables validation, safe storage, structured display, and meaningful human review. The consultant sees organised scores and can make an informed decision in under 2 minutes.

---

## 4. Known Limitations of the POC vs. a Production System

| Limitation | Impact | Production solution |
|---|---|---|
| No real-time German job vacancy data | Recommendations use static model knowledge | RAG pipeline ingesting DAAD and BIBB live data (UC-07) |
| Scoring depends on student self-report | Student may misrepresent German level | Goethe Institut certificate verification integration |
| No Spanish language version | Excludes students not comfortable in English | i18n frontend with Spanish translations (Month 3) |
| Admin password hardcoded | Security risk at scale | JWT authentication with Supabase Auth |
| Single LLM provider | Anthropic outage = service unavailable | Abstract client creation behind a factory function; provider swap is a localised change |
| No rate limiting | Vulnerable to abuse at scale | Redis rate limiting before public launch |
| Temperature 0.3, not zero | Minor score variation between identical profiles | Deterministic caching layer for repeated profiles |

---

## 5. How to Reproduce / Run the POC

### Prerequisites
- Python 3.11+, Node.js 18+
- Supabase account (free tier)
- Anthropic API key

### Clone and set up
```bash
git clone https://github.com/Lucas-Barrios/klar-advisory.git
cd klar-advisory

# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY

# Run Supabase SQL schema (see backend/schema.sql)

venv/bin/uvicorn main:app --reload
# API at http://localhost:8000, docs at http://localhost:8000/docs

# Frontend (new terminal)
cd ../frontend
npm install
cp .env.local.example .env.local
# Fill in NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY,
# NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# App at http://localhost:3001
```

### Test via API
```bash
curl -X POST http://localhost:8000/api/diagnostic/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Maria García",
    "email": "maria@test.com",
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
  }'
```

Expected:
```json
{
  "diagnostic_id": "uuid",
  "status": "pending",
  "message": "Your diagnostic is being reviewed..."
}
```

---

*POC Documentation · Klar · Ironhack Berlin AI & Integration Consulting · June 2026*
