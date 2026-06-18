from fastapi import APIRouter, HTTPException, BackgroundTasks, Header, Request, status
from models.schemas import DocumentFactoryRequest, StudentProfileInput, DiagnosticResponse
from agents.germany_diagnostic import DiagnosticAIError, run_diagnostic
from database import get_supabase
from pydantic import BaseModel, Field, field_validator
from services.ai_observability import (
    persist_usage_event,
    usage_event_with_context,
)
from services.admin_auth import extract_bearer_token
from services.diagnostic_versions import (
    DIAGNOSTIC_PROMPT_VERSION,
    DIAGNOSTIC_RUBRIC_VERSION,
    MATCH_PROMPT_VERSION,
)
from services.progress_auth import (
    generate_progress_token,
    hash_progress_token,
    verify_progress_token,
)
from services.rate_limiter import limiter
from services.redaction import mask_email_for_log, mask_name_for_log
import httpx
import logging
import os

router = APIRouter()


def record_ai_usage(
    supabase,
    usage_event: dict | None,
    *,
    diagnostic_id: str | None,
    student_id: str | None,
) -> bool:
    if not usage_event:
        return False
    event = usage_event_with_context(
        usage_event,
        diagnostic_id=diagnostic_id,
        student_id=student_id,
    )
    return persist_usage_event(supabase, event)


@router.post("/", response_model=DiagnosticResponse)
@limiter.limit("5/hour")
async def create_diagnostic(request: Request, student: StudentProfileInput, background_tasks: BackgroundTasks):
    if not student.consent_given:
        raise HTTPException(
            status_code=422,
            detail="Submission rejected: data processing consent is required.",
        )

    supabase = get_supabase()
    student_id = None
    diagnostic_id = None
    ai_usage_event = None
    usage_logged = False
    try:
        from datetime import datetime, timezone as _tz
        student_data = student.model_dump(mode="json")
        if student_data.get("consent_timestamp") is None:
            student_data["consent_timestamp"] = datetime.now(_tz.utc).isoformat()

        # Save student
        s = supabase.table("students").insert(student_data).execute()
        student_id = s.data[0]["id"]

        # Run agent
        output = run_diagnostic(student_data)
        ai_usage_event = output.get("_ai_usage")

        # Save diagnostic
        progress_token = generate_progress_token()
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
            "next_step_message": output.get("next_step_message"),
            "roadmap": output["roadmap"],
            "recommendations": output["recommendations"],
            "raw_output": output.get("raw_output", ""),
            "status": "pending",
            "diagnostic_prompt_version": DIAGNOSTIC_PROMPT_VERSION,
            "diagnostic_rubric_version": DIAGNOSTIC_RUBRIC_VERSION,
            "ai_model": (ai_usage_event or {}).get("model"),
            "progress_token_hash": hash_progress_token(progress_token),
        }).execute()
        diagnostic_id = d.data[0]["id"]
        try:
            usage_logged = record_ai_usage(
                supabase,
                ai_usage_event,
                diagnostic_id=diagnostic_id,
                student_id=student_id,
            )
        except Exception:
            usage_logged = False

        # Audit log
        supabase.table("audit_log").insert({
            "diagnostic_id": diagnostic_id,
            "action": "diagnostic_created",
            "actor": "system",
            "details": {"pathway": student.pathway}
        }).execute()

        # Notify n8n in background
        background_tasks.add_task(
            notify_n8n, diagnostic_id, student.name, student.email, student.pathway
        )

        # Trigger position matching in background for ausbildung pathway
        if student.pathway == "ausbildung":
            background_tasks.add_task(
                run_ausbildung_matching, diagnostic_id, student_id, student_data
            )

        return DiagnosticResponse(
            diagnostic_id=diagnostic_id,
            status="pending",
            message="Your diagnostic is being reviewed. You will receive your results by email once approved.",
            progress_token=progress_token,
        )

    except DiagnosticAIError as e:
        if student_id:
            try:
                supabase.table("students").update(
                    {"ai_status": "diagnostic_failed"}
                ).eq("id", student_id).execute()
            except Exception:
                pass
            record_ai_usage(
                supabase,
                e.usage_event,
                diagnostic_id=None,
                student_id=student_id,
            )
        raise HTTPException(
            status_code=502,
            detail="Diagnostic AI service is temporarily unavailable. Please try again later.",
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("=== DIAGNOSTIC CREATION FAILED ===")
        print(traceback.format_exc())
        if ai_usage_event and not usage_logged and student_id:
            try:
                record_ai_usage(
                    supabase,
                    ai_usage_event,
                    diagnostic_id=diagnostic_id,
                    student_id=student_id,
                )
            except Exception:
                pass
        raise HTTPException(
            status_code=500,
            detail=f"Could not create diagnostic: {str(e)}",
        ) from e


def public_diagnostic_result(record: dict) -> dict:
    diagnostic_id = record.get("id")
    status = record.get("status")
    student = record.get("students") or {}
    display_name = student.get("name") or student.get("full_name")
    if status == "rejected":
        return {
            "diagnostic_id": diagnostic_id,
            "status": "not_available",
            "message": "This diagnostic result is not available.",
        }
    if status == "pending":
        return {
            "diagnostic_id": diagnostic_id,
            "status": "pending",
            "message": "Your diagnostic is still under review.",
        }
    return {
        "diagnostic_id": diagnostic_id,
        "id": diagnostic_id,
        "status": status,
        "overall_score": record.get("overall_score"),
        "dimension_scores": {
            "language": record.get("language_score"),
            "education": record.get("education_score"),
            "pathway_fit": record.get("pathway_fit_score"),
            "timeline": record.get("timeline_score"),
            "financial": record.get("financial_score"),
            "documentation": record.get("documentation_score"),
        },
        "summary": record.get("summary"),
        "next_step_message": record.get("next_step_message"),
        "roadmap": record.get("roadmap"),
        "recommendations": record.get("recommendations"),
        "completed_steps": record.get("completed_steps") or [],
        "matches_unlocked": record.get("matches_unlocked", False),
        "documents_unlocked": record.get("documents_unlocked", False),
        "student": {
            "name": display_name,
        },
        "students": {
            "name": display_name,
            "full_name": display_name,
            "pathway": student.get("pathway"),
        },
    }


@router.get("/{diagnostic_id}/result")
def get_diagnostic_result(diagnostic_id: str):
    supabase = get_supabase()
    try:
        # Fetch only the student fields the public view actually uses (name + pathway).
        # Email is not returned by public_diagnostic_result; omitting it here enforces
        # data minimisation at the query layer.
        result = supabase.table("diagnostics").select(
            "*, students(name,full_name,pathway)"
        ).eq("id", diagnostic_id).single().execute()
    except Exception as e:
        raise HTTPException(status_code=404, detail="Diagnostic not found") from e

    if not result.data:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    return public_diagnostic_result(result.data)


@router.get("/{diagnostic_id}/matches")
def get_public_matches(diagnostic_id: str):
    supabase = get_supabase()
    try:
        diagnostic = supabase.table("diagnostics").select(
            "id, status, matches_unlocked"
        ).eq("id", diagnostic_id).single().execute()
    except Exception as e:
        raise HTTPException(status_code=404, detail="Diagnostic not found") from e

    if not diagnostic.data or diagnostic.data.get("status") != "approved":
        raise HTTPException(status_code=404, detail="Matches not available")

    result = supabase.table("ausbildung_matches").select("*").eq(
        "diagnostic_id", diagnostic_id
    ).execute()

    if not result.data:
        return None

    match_data = result.data[0]
    all_positions = match_data.get("matched_positions") or []

    if diagnostic.data.get("matches_unlocked"):
        return {**match_data, "matches_unlocked": True, "locked_count": 0}

    locked_count = max(0, len(all_positions) - 1)
    return {
        **match_data,
        "matched_positions": all_positions[:1],
        "locked_count": locked_count,
        "matches_unlocked": False,
    }


class ProgressUpdate(BaseModel):
    completed_steps: list[int] = Field(default_factory=list, max_length=24)

    @field_validator("completed_steps")
    @classmethod
    def validate_completed_steps(cls, value: list[int]) -> list[int]:
        if any(step < 0 or step > 24 for step in value):
            raise ValueError("completed steps must be between 0 and 24")
        return sorted(set(value))


@router.patch("/{diagnostic_id}/progress")
def update_progress(
    diagnostic_id: str,
    update: ProgressUpdate,
    authorization: str | None = Header(default=None),
):
    supabase = get_supabase()
    try:
        diagnostic = supabase.table("diagnostics").select(
            "id, progress_token_hash"
        ).eq("id", diagnostic_id).single().execute()

        if not diagnostic.data:
            raise HTTPException(status_code=404, detail="Diagnostic not found")

        token = extract_bearer_token(authorization)
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing progress authorization",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not verify_progress_token(
            token,
            (diagnostic.data or {}).get("progress_token_hash"),
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid progress authorization",
            )

        result = supabase.table("diagnostics").update({
            "completed_steps": update.completed_steps
        }).eq("id", diagnostic_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Diagnostic not found")

        return {"status": "ok", "completed_steps": update.completed_steps}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{diagnostic_id}/generate-documents")
def generate_documents_endpoint(diagnostic_id: str, body: DocumentFactoryRequest = DocumentFactoryRequest()):
    supabase = get_supabase()
    try:
        diagnostic = supabase.table("diagnostics").select(
            "*, students(*)"
        ).eq("id", diagnostic_id).single().execute()
    except Exception as e:
        raise HTTPException(status_code=404, detail="Diagnostic not found") from e

    if not (diagnostic.data or {}).get("documents_unlocked"):
        raise HTTPException(status_code=402, detail="Payment required to generate documents")

    student_data = (diagnostic.data or {}).get("students") or {}
    doc_student_id = (diagnostic.data or {}).get("student_id")

    try:
        from agents.document_factory import generate_documents
        documents = generate_documents(
            student_data,
            diagnostic_id=diagnostic_id,
            student_id=doc_student_id,
            target_language=body.target_language,
        )
        doc_usage = documents.pop("_ai_usage", None)
        if doc_usage:
            try:
                record_ai_usage(
                    supabase,
                    doc_usage,
                    diagnostic_id=diagnostic_id,
                    student_id=doc_student_id,
                )
            except Exception:
                pass
        return documents
    except Exception as e:
        import traceback
        print("=== DOCUMENT GENERATION FAILED ===")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="Document generation is temporarily unavailable. Please try again later.",
        )


def run_ausbildung_matching(diagnostic_id: str, student_id: str, student_data: dict) -> None:
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    supabase = get_supabase()
    try:
        from agents.ausbildung_matcher import match_positions
        match_result = match_positions(
            student_data,
            diagnostic_id=diagnostic_id,
            student_id=student_id,
        )
        supabase.table("ausbildung_matches").insert({
            "diagnostic_id": diagnostic_id,
            "matched_positions": match_result.get("matches", []),
            "reasoning_summary": match_result.get("overall_summary", ""),
            "status": "pending",
            "match_prompt_version": MATCH_PROMPT_VERSION,
        }).execute()
    except Exception as e:
        _logger.warning("Position matching failed (non-blocking): %s", type(e).__name__)
        try:
            supabase.table("audit_log").insert({
                "diagnostic_id": diagnostic_id,
                "action": "ausbildung_matching_failed",
                "actor": "system",
                "details": {"error_type": type(e).__name__},
            }).execute()
        except Exception:
            pass


_notify_logger = logging.getLogger(__name__)


async def notify_student_approved(diagnostic_id: str, name: str, email: str) -> None:
    if not email or "@" not in email:
        _notify_logger.warning(
            "Skipping approval email for diagnostic %s — no valid email",
            diagnostic_id,
        )
        return

    resend_key = os.getenv("RESEND_API_KEY")
    if not resend_key:
        _notify_logger.warning("RESEND_API_KEY not set — skipping approval email")
        return

    from_addr = os.getenv("RESEND_FROM_EMAIL", "hello@mail.kairosconsulting.co")
    frontend_url = os.getenv("FRONTEND_URL", "https://klar-advisory.vercel.app")
    results_url = f"{frontend_url}/results/{diagnostic_id}"
    first_name = name.split()[0] if name else "there"

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0F1117;font-family:system-ui,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 20px;">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#111827;border-radius:16px;overflow:hidden;
                    border:1px solid rgba(255,255,255,0.08);">

        <!-- Header bar -->
        <tr><td style="background:#2563EB;padding:20px 32px;">
          <span style="font-size:20px;font-weight:800;color:#fff;
                       letter-spacing:-0.03em;">Klar</span>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:32px;">
          <p style="margin:0 0 8px;font-size:22px;font-weight:700;
                    color:#F9FAFB;letter-spacing:-0.02em;">
            Your results are ready, {first_name} &#x1F389;
          </p>
          <p style="margin:0 0 24px;font-size:15px;color:#9CA3AF;
                    line-height:1.6;">
            A Klar consultant has reviewed your Germany Readiness
            Diagnostic. Your personalised score, roadmap, and next
            steps are ready to view.
          </p>

          <!-- CTA button -->
          <a href="{results_url}"
             style="display:inline-block;background:#2563EB;
                    color:#fff;font-weight:700;font-size:15px;
                    padding:14px 28px;border-radius:9999px;
                    text-decoration:none;letter-spacing:-0.01em;">
            View My Results &#x2192;
          </a>

          <!-- Divider -->
          <hr style="margin:28px 0;border:none;
                     border-top:1px solid rgba(255,255,255,0.08);">

          <p style="margin:0;font-size:12px;color:#6B7280;
                    line-height:1.6;">
            This is a human-reviewed result &#x2014; not a raw AI output.
            A Klar consultant has read your diagnostic and confirmed
            it before it was approved.
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:16px 32px;
                       border-top:1px solid rgba(255,255,255,0.06);">
          <p style="margin:0;font-size:11px;color:#4B5563;">
            Klar &#xB7; Germany Readiness Platform &#xB7;
            <a href="{frontend_url}" style="color:#4B5563;">
              klar-advisory.vercel.app
            </a>
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"Klar <{from_addr}>",
                    "to": [email],
                    "subject": "Your Klar results are ready ✓",
                    "html": html,
                },
            )
        if resp.status_code >= 400:
            _notify_logger.warning(
                "Approval email send failed: status=%s body=%s",
                resp.status_code,
                resp.text[:200],
            )
        else:
            _notify_logger.info(
                "Approval email sent to %s for diagnostic %s",
                mask_email_for_log(email),
                diagnostic_id,
            )
    except Exception as exc:
        _notify_logger.warning("Approval email failed: %s", exc)


async def notify_n8n(diagnostic_id: str, name: str, email: str, pathway: str):
    webhook = os.getenv("N8N_WEBHOOK_URL")
    print(f"[N8N DEBUG] notify_n8n called for diagnostic {diagnostic_id}")
    print(f"[N8N DEBUG] webhook env var resolved to: {webhook!r}")

    if not webhook:
        print(f"[N8N DEBUG] No webhook configured, returning early")
        return

    print(f"[N8N DEBUG] Attempting webhook call to: {webhook}")
    try:
        async with httpx.AsyncClient() as c:
            response = await c.post(webhook, json={
                "diagnostic_id": diagnostic_id,
                "student_name": name,
                "student_email": email,
                "pathway": pathway,
                "review_url": os.getenv("ADMIN_URL", "http://localhost:3001") + "/admin"
            })
            print(f"[N8N DEBUG] Webhook succeeded, status: {response.status_code}")
    except Exception as e:
        print(f"[N8N DEBUG] Webhook FAILED: {type(e).__name__}: {e}")
