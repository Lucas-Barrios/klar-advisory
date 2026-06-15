from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.schemas import StudentProfileInput, DiagnosticResponse
from agents.germany_diagnostic import run_diagnostic
from database import get_supabase
import httpx, os

router = APIRouter()

@router.post("/", response_model=DiagnosticResponse)
async def create_diagnostic(student: StudentProfileInput, background_tasks: BackgroundTasks):
    supabase = get_supabase()
    try:
        student_data = student.model_dump()

        # Save student
        s = supabase.table("students").insert(student_data).execute()
        student_id = s.data[0]["id"]

        # Run agent
        output = run_diagnostic(student_data)

        # Save diagnostic
        d = supabase.table("diagnostics").insert({
            "student_id": student_id,
            "overall_score": output["overall_score"],
            "language_score": output["language_score"],
            "education_score": output["education_score"],
            "pathway_fit_score": output["pathway_fit_score"],
            "timeline_score": output["timeline_score"],
            "financial_score": output["financial_score"],
            "documentation_score": output["documentation_score"],
            "summary": output["summary"],
            "roadmap": output["roadmap"],
            "recommendations": output["recommendations"],
            "raw_output": output.get("raw_output", ""),
            "status": "pending"
        }).execute()
        diagnostic_id = d.data[0]["id"]

        # Audit log
        supabase.table("audit_log").insert({
            "diagnostic_id": diagnostic_id,
            "action": "diagnostic_created",
            "actor": "system",
            "details": {"student_email": student.email, "pathway": student.pathway}
        }).execute()

        # Notify n8n in background
        background_tasks.add_task(
            notify_n8n, diagnostic_id, student.name, student.email, student.pathway
        )

        return DiagnosticResponse(
            diagnostic_id=diagnostic_id,
            status="pending",
            message="Your diagnostic is being reviewed. You will receive your results by email once approved."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def notify_n8n(diagnostic_id: str, name: str, email: str, pathway: str):
    webhook = os.getenv("N8N_WEBHOOK_URL")
    if not webhook:
        return
    try:
        async with httpx.AsyncClient() as c:
            await c.post(webhook, json={
                "diagnostic_id": diagnostic_id,
                "student_name": name,
                "student_email": email,
                "pathway": pathway,
                "review_url": f"{os.getenv('ADMIN_URL', 'http://localhost:3001')}/admin"
            })
    except Exception:
        pass