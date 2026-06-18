import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from models.schemas import (
    EvaluationDatasetCreate,
    EvaluationExampleCreate,
    EvaluationExampleFromDiagnosticCreate,
    EvaluationExperimentCompareRequest,
    EvaluationExperimentCreate,
    EvaluationResultCreate,
    EvaluationRunCreate,
    ReviewAction,
)
from database import get_supabase
from datetime import datetime, timezone
from services.ai_observability import aggregate_monthly_usage
from services.admin_auth import require_admin_authorization
from services.evaluation import (
    add_evaluation_example,
    add_example_from_diagnostic,
    complete_evaluation_run,
    create_evaluation_dataset,
    create_evaluation_run,
    get_evaluation_run_report,
    get_evaluation_summary,
    list_evaluation_datasets,
    record_evaluation_result,
)
from routers.diagnostic import notify_student_approved
from services.redaction import redact_sensitive_text
from services.statistical_evaluation import (
    create_evaluation_experiment,
    get_evaluation_experiment,
    list_evaluation_experiments,
    run_evaluation_experiment_comparison,
)

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_admin_authorization)])


def student_redaction_identifiers(student: dict | None) -> list[str | None]:
    if not student:
        return []
    return [
        student.get("name"),
        student.get("full_name"),
        student.get("email"),
    ]

@router.get("/diagnostics")
def get_pending():
    supabase = get_supabase()
    result = supabase.table("diagnostics").select(
        "*, students(*)"
    ).eq("status", "pending").order("created_at", desc=False).execute()
    return result.data

@router.get("/diagnostics/{diagnostic_id}")
def get_diagnostic(diagnostic_id: str):
    supabase = get_supabase()
    result = supabase.table("diagnostics").select(
        "*, students(*)"
    ).eq("id", diagnostic_id).single().execute()
    return result.data

@router.post("/diagnostics/{diagnostic_id}/review")
async def review_diagnostic(diagnostic_id: str, action: ReviewAction, background_tasks: BackgroundTasks):
    supabase = get_supabase()
    diagnostic = supabase.table("diagnostics").select(
        "id, students(name, full_name, email)"
    ).eq("id", diagnostic_id).single().execute()
    if not diagnostic.data:
        raise HTTPException(status_code=404, detail="Diagnostic not found")

    student = (diagnostic.data or {}).get("students") or {}
    redaction_identifiers = student_redaction_identifiers(student)
    sanitized_notes = redact_sensitive_text(
        action.reviewer_notes,
        identifiers=redaction_identifiers,
        redact_name_like=True,
    )
    sanitized_correction_notes = redact_sensitive_text(
        action.reviewer_correction_notes or action.reviewer_notes,
        identifiers=redaction_identifiers,
        redact_name_like=True,
    )
    sanitized_rejection_reason = redact_sensitive_text(
        action.rejection_reason,
        identifiers=redaction_identifiers,
        redact_name_like=True,
    )
    reviewer_decision = action.reviewer_decision or action.status
    supabase.table("diagnostics").update({
        "status": action.status,
        "reviewer_notes": action.reviewer_notes,
        "reviewer_decision": reviewer_decision,
        "reviewer_correction_notes": (
            action.reviewer_correction_notes or action.reviewer_notes
        ),
        "reviewer_confidence": action.reviewer_confidence,
        "rejection_reason": action.rejection_reason,
        "review_duration_seconds": action.review_duration_seconds,
        "reviewed_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", diagnostic_id).execute()

    try:
        supabase.table("ausbildung_matches").update({
            "status": action.status,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("diagnostic_id", diagnostic_id).execute()
    except Exception as e:
        logger.warning("Failed to update ausbildung_matches status: %s", e)

    supabase.table("audit_log").insert({
        "diagnostic_id": diagnostic_id,
        "action": f"review_{action.status}",
        "actor": "consultant",
        "details": {
            "notes": sanitized_notes,
            "reviewer_decision": reviewer_decision,
            "reviewer_confidence": action.reviewer_confidence,
            "rejection_reason": sanitized_rejection_reason,
            "review_duration_seconds": action.review_duration_seconds,
            "reviewer_correction_notes": sanitized_correction_notes,
        }
    }).execute()

    if action.status == "approved":
        student_name = student.get("name") or student.get("full_name") or ""
        student_email = student.get("email") or ""
        if not student_email:
            logger.warning(
                "Approval for diagnostic %s — student email is empty, "
                "notification will be skipped",
                diagnostic_id,
            )
        background_tasks.add_task(
            notify_student_approved, diagnostic_id, student_name, student_email
        )

    return {"status": "ok", "message": f"Diagnostic {action.status}"}


@router.get("/evaluation/datasets")
def get_evaluation_datasets():
    supabase = get_supabase()
    try:
        return list_evaluation_datasets(supabase)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not load evaluation datasets") from e


@router.post("/evaluation/datasets")
def post_evaluation_dataset(dataset: EvaluationDatasetCreate):
    supabase = get_supabase()
    try:
        return create_evaluation_dataset(supabase, dataset.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not create evaluation dataset") from e


@router.post("/evaluation/examples")
def post_evaluation_example(example: EvaluationExampleCreate):
    supabase = get_supabase()
    try:
        return add_evaluation_example(supabase, example.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not create evaluation example") from e


@router.post("/evaluation/examples/from-diagnostic/{diagnostic_id}")
def post_evaluation_example_from_diagnostic(
    diagnostic_id: str,
    payload: EvaluationExampleFromDiagnosticCreate,
):
    supabase = get_supabase()
    try:
        return add_example_from_diagnostic(
            supabase,
            diagnostic_id,
            payload.model_dump(exclude_none=True),
        )
    except ValueError as e:
        message = str(e)
        status_code = 404 if "not found" in message else 400
        raise HTTPException(status_code=status_code, detail=message) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Could not create evaluation example from diagnostic",
        ) from e


@router.post("/evaluation/runs")
def post_evaluation_run(run: EvaluationRunCreate):
    supabase = get_supabase()
    try:
        return create_evaluation_run(supabase, run.model_dump(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not create evaluation run") from e


@router.post("/evaluation/runs/{run_id}/results")
def post_evaluation_result(run_id: str, result: EvaluationResultCreate):
    supabase = get_supabase()
    try:
        return record_evaluation_result(
            supabase,
            run_id,
            result.model_dump(exclude_none=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not record evaluation result") from e


@router.post("/evaluation/runs/{run_id}/complete")
def post_complete_evaluation_run(run_id: str):
    supabase = get_supabase()
    try:
        return complete_evaluation_run(supabase, run_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not complete evaluation run") from e


@router.get("/evaluation/runs/{run_id}")
def get_evaluation_run(run_id: str):
    supabase = get_supabase()
    try:
        return get_evaluation_run_report(supabase, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not load evaluation run") from e


@router.get("/evaluation/summary")
def get_admin_evaluation_summary():
    supabase = get_supabase()
    try:
        return get_evaluation_summary(supabase)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not load evaluation summary") from e


@router.post("/evaluation/experiments")
def post_evaluation_experiment(experiment: EvaluationExperimentCreate):
    supabase = get_supabase()
    try:
        return create_evaluation_experiment(
            supabase,
            experiment.model_dump(exclude_none=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not create evaluation experiment") from e


@router.get("/evaluation/experiments")
def get_evaluation_experiments():
    supabase = get_supabase()
    try:
        return list_evaluation_experiments(supabase)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not load evaluation experiments") from e


@router.get("/evaluation/experiments/{experiment_id}")
def get_evaluation_experiment_detail(experiment_id: str):
    supabase = get_supabase()
    try:
        return get_evaluation_experiment(supabase, experiment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not load evaluation experiment") from e


@router.post("/evaluation/experiments/{experiment_id}/compare")
def post_evaluation_experiment_compare(
    experiment_id: str,
    request: EvaluationExperimentCompareRequest | None = None,
):
    supabase = get_supabase()
    try:
        return run_evaluation_experiment_comparison(
            supabase,
            experiment_id,
            (request.model_dump(exclude_none=True) if request else {}),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not compare evaluation experiment") from e

@router.post("/diagnostics/{diagnostic_id}/mark-booked")
def mark_booked(diagnostic_id: str):
    supabase = get_supabase()
    result = supabase.table("diagnostics").select("id").eq("id", diagnostic_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    supabase.table("diagnostics").update({
        "consultation_booked": True,
        "consultation_booked_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", diagnostic_id).execute()
    supabase.table("audit_log").insert({
        "diagnostic_id": diagnostic_id,
        "action": "consultation_booked",
        "actor": "consultant",
        "details": {},
    }).execute()
    return {"status": "ok"}


@router.post("/refresh-positions")
def refresh_positions():
    from services.ausbildung_cache import refresh_all_positions
    results = refresh_all_positions()
    return {"status": "ok", "refreshed": results}


@router.get("/diagnostics/{diagnostic_id}/matches")
def get_diagnostic_matches(diagnostic_id: str):
    supabase = get_supabase()
    result = supabase.table("ausbildung_matches").select("*").eq(
        "diagnostic_id", diagnostic_id
    ).execute()
    return result.data[0] if result.data else None


@router.get("/stats")
def get_stats():
    supabase = get_supabase()

    pending = supabase.table("diagnostics").select(
        "id", count="exact"
    ).eq("status", "pending").execute()

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
    approved_today = supabase.table("diagnostics").select(
        "id", count="exact"
    ).eq("status", "approved").gte("reviewed_at", today_start).execute()

    total = supabase.table("diagnostics").select(
        "id", count="exact"
    ).execute()

    approved_count_result = supabase.table("diagnostics").select(
        "id", count="exact"
    ).eq("status", "approved").execute()
    approved_count = approved_count_result.count or 0

    booked_count_result = supabase.table("diagnostics").select(
        "id", count="exact"
    ).eq("consultation_booked", True).execute()
    booked_count = booked_count_result.count or 0

    conversion_rate = round((booked_count / approved_count) * 100, 1) if approved_count > 0 else 0

    return {
        "pending": pending.count or 0,
        "approved_today": approved_today.count or 0,
        "total": total.count or 0,
        "approved_count": approved_count,
        "booked_count": booked_count,
        "conversion_rate": conversion_rate,
    }


def month_window(now: datetime) -> tuple[str, str]:
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    next_month = next_month.replace(hour=0, minute=0, second=0, microsecond=0)
    return month_start.isoformat(), next_month.isoformat()


def fetch_monthly_usage_events(supabase, month_start: str, next_month: str) -> list[dict]:
    try:
        result = supabase.table("ai_usage_events").select(
            "*"
        ).gte("created_at", month_start).lt("created_at", next_month).execute()
        return result.data or []
    except Exception as primary_error:
        logger.warning(
            "ai_usage_events query failed; attempting audit_log telemetry fallback",
            extra={"error_type": primary_error.__class__.__name__},
        )
        try:
            audit_rows = supabase.table("audit_log").select(
                "created_at, details"
            ).eq("action", "ai_usage_event").gte(
                "created_at", month_start
            ).lt("created_at", next_month).execute()
        except Exception as fallback_error:
            logger.error(
                "audit_log telemetry fallback query failed",
                extra={
                    "primary_error_type": primary_error.__class__.__name__,
                    "fallback_error_type": fallback_error.__class__.__name__,
                },
            )
            raise
        events = []
        for row in audit_rows.data or []:
            telemetry = (row.get("details") or {}).get("telemetry")
            if telemetry:
                telemetry.setdefault("created_at", row.get("created_at"))
                events.append(telemetry)
        return events


@router.get("/tco")
def get_tco():
    supabase = get_supabase()
    now = datetime.now(timezone.utc)
    month_start, next_month = month_window(now)
    try:
        events = fetch_monthly_usage_events(supabase, month_start, next_month)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not load TCO metrics") from e
    return aggregate_monthly_usage(events, now=now)
