from fastapi import APIRouter, HTTPException
from models.schemas import ReviewAction
from database import get_supabase
from datetime import datetime, timezone

router = APIRouter()

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
def review_diagnostic(diagnostic_id: str, action: ReviewAction):
    supabase = get_supabase()
    supabase.table("diagnostics").update({
        "status": action.status,
        "reviewer_notes": action.reviewer_notes,
        "reviewed_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", diagnostic_id).execute()

    supabase.table("audit_log").insert({
        "diagnostic_id": diagnostic_id,
        "action": f"review_{action.status}",
        "actor": "consultant",
        "details": {"notes": action.reviewer_notes}
    }).execute()

    return {"status": "ok", "message": f"Diagnostic {action.status}"}