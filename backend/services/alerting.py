from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_ERROR_THRESHOLD_COUNT = 3
_DEFAULT_ERROR_WINDOW_MINUTES = 15
# $5/day ≈ 60 full-kit requests at pilot scale (~$0.08 each across UC-01 + UC-02 + UC-04).
_DEFAULT_COST_THRESHOLD_DAILY = 5.00
_COOLDOWN_MINUTES = 60


def _is_on_cooldown(supabase, alert_type: str) -> bool:
    """Return True if an alert of this type was sent within the last cooldown window."""
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=_COOLDOWN_MINUTES)).isoformat()
    try:
        result = (
            supabase.table("audit_log")
            .select("details")
            .eq("action", "alert_sent")
            .gte("created_at", cutoff)
            .execute()
        )
        return any(
            (row.get("details") or {}).get("alert_type") == alert_type
            for row in (result.data or [])
        )
    except Exception:
        return False


def _record_alert_sent(supabase, alert_type: str, extra: dict) -> None:
    try:
        supabase.table("audit_log").insert({
            "action": "alert_sent",
            "actor": "system",
            "details": {"alert_type": alert_type, **extra},
        }).execute()
    except Exception as exc:
        logger.warning("Could not write alert_sent to audit_log: %s", exc)


def _send_alert_email(subject: str, body_html: str) -> None:
    resend_key = os.getenv("RESEND_API_KEY")
    to_email = os.getenv("ALERT_EMAIL_TO")
    from_addr = os.getenv("RESEND_FROM_EMAIL", "noreply@klar-advisory.com")

    if not resend_key or not to_email:
        logger.warning(
            "Alert suppressed — RESEND_API_KEY or ALERT_EMAIL_TO not set (subject: %s)",
            subject,
        )
        return

    with httpx.Client(timeout=10) as http:
        resp = http.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"Klar Alerts <{from_addr}>",
                "to": [to_email],
                "subject": subject,
                "html": body_html,
            },
        )
    if resp.status_code >= 400:
        logger.warning(
            "Alert email send failed: status=%s body=%s", resp.status_code, resp.text[:200]
        )
    else:
        logger.info("Alert email sent: %s", subject)


def check_and_alert_error_rate(supabase) -> None:
    """Query ai_usage_events for recent failures. Email if threshold is crossed."""
    try:
        threshold_count = int(
            os.getenv("ALERT_ERROR_THRESHOLD_COUNT", str(_DEFAULT_ERROR_THRESHOLD_COUNT))
        )
        window_minutes = int(
            os.getenv("ALERT_ERROR_THRESHOLD_WINDOW_MINUTES", str(_DEFAULT_ERROR_WINDOW_MINUTES))
        )
        window_start = (
            datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        ).isoformat()

        result = (
            supabase.table("ai_usage_events")
            .select("id")
            .eq("success", False)
            .gte("created_at", window_start)
            .execute()
        )
        failure_count = len(result.data or [])

        if failure_count < threshold_count:
            return

        if _is_on_cooldown(supabase, "error_rate"):
            return

        subject = f"⚠️ Klar Alert: {failure_count} failures in {window_minutes} minutes"
        body = (
            f"<p><strong>{failure_count} AI call failures</strong> detected in the last "
            f"{window_minutes} minutes (threshold: {threshold_count}).</p>"
            f"<p>Check <code>ai_usage_events</code> and server logs for details.</p>"
        )
        _send_alert_email(subject, body)
        _record_alert_sent(supabase, "error_rate", {
            "failure_count": failure_count,
            "window_minutes": window_minutes,
        })
    except Exception as exc:
        logger.warning("check_and_alert_error_rate failed (non-blocking): %s", exc)


def check_and_alert_cost(supabase) -> None:
    """Sum today's estimated_cost in ai_usage_events. Email if daily threshold exceeded."""
    try:
        threshold = float(
            os.getenv("ALERT_COST_THRESHOLD_DAILY", str(_DEFAULT_COST_THRESHOLD_DAILY))
        )
        day_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

        result = (
            supabase.table("ai_usage_events")
            .select("estimated_cost")
            .gte("created_at", day_start)
            .execute()
        )
        daily_cost = sum(
            float(row.get("estimated_cost") or 0.0) for row in (result.data or [])
        )

        if daily_cost < threshold:
            return

        if _is_on_cooldown(supabase, "cost"):
            return

        subject = (
            f"⚠️ Klar Alert: daily cost threshold exceeded "
            f"(${daily_cost:.4f} of ${threshold:.2f})"
        )
        body = (
            f"<p>Today’s estimated AI spend is <strong>${daily_cost:.4f}</strong>, "
            f"exceeding the configured threshold of <strong>${threshold:.2f}</strong>.</p>"
            f"<p>Check <code>ai_usage_events</code> or the "
            f"<code>/api/admin/tco</code> endpoint for a breakdown.</p>"
        )
        _send_alert_email(subject, body)
        _record_alert_sent(supabase, "cost", {
            "daily_cost": round(daily_cost, 6),
            "threshold": threshold,
        })
    except Exception as exc:
        logger.warning("check_and_alert_cost failed (non-blocking): %s", exc)
