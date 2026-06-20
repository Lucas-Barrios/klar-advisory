from __future__ import annotations

import calendar
import logging
import math
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from services.alerting import check_and_alert_cost, check_and_alert_error_rate
from services.request_id import get_request_id


AI_PROVIDER = "anthropic"
AI_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
# Haiku is sufficient for cheap classification/routing calls (5-way sector mapping).
# Use the dated snapshot ID: Haiku 4.5 predates the 4.6 generation so its canonical
# pinned form is claude-haiku-4-5-20251001. The bare "claude-haiku-4-5" is a
# convenience alias, not the pinned snapshot (per platform.claude.com/docs/en/about-claude/models/model-ids-and-versions).
AI_MODEL_HAIKU = os.getenv("ANTHROPIC_HAIKU_MODEL", "claude-haiku-4-5-20251001")
REQUEST_TYPE_GERMANY_DIAGNOSTIC = "germany_diagnostic"
REQUEST_TYPE_AUSBILDUNG_SECTOR = "ausbildung_sector"
REQUEST_TYPE_AUSBILDUNG_MATCH = "ausbildung_match"
REQUEST_TYPE_DOCUMENT_FACTORY = "document_factory"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelPricing:
    provider: str
    input_usd_per_mtok: float
    output_usd_per_mtok: float


MODEL_PRICING: dict[str, ModelPricing] = {
    # Anthropic lists Claude Sonnet 4.6 at $3/MTok input and $15/MTok output.
    "claude-sonnet-4-6": ModelPricing(AI_PROVIDER, 3.0, 15.0),
    "claude-sonnet-4.6": ModelPricing(AI_PROVIDER, 3.0, 15.0),
    "claude-sonnet-4-5": ModelPricing(AI_PROVIDER, 3.0, 15.0),
    # Claude Haiku 4.5 at $1/MTok input and $5/MTok output.
    "claude-haiku-4-5": ModelPricing(AI_PROVIDER, 1.0, 5.0),
    "claude-haiku-4-5-20251001": ModelPricing(AI_PROVIDER, 1.0, 5.0),
}

PII_TELEMETRY_KEYS = {
    "prompt",
    "raw_prompt",
    "student_name",
    "student_email",
    "email",
    "name",
    "profile",
    "answers",
    "full_profile",
    "raw_output",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def estimate_tokens_from_text(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def get_model_pricing(model: str, provider: str = AI_PROVIDER) -> ModelPricing:
    env_input = os.getenv("ANTHROPIC_INPUT_USD_PER_MTOK")
    env_output = os.getenv("ANTHROPIC_OUTPUT_USD_PER_MTOK")
    if provider == AI_PROVIDER and env_input and env_output:
        try:
            return ModelPricing(provider, float(env_input), float(env_output))
        except ValueError:
            pass

    return MODEL_PRICING.get(model, ModelPricing(provider, 0.0, 0.0))


def calculate_estimated_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    provider: str = AI_PROVIDER,
) -> float:
    pricing = get_model_pricing(model, provider)
    input_cost = (max(input_tokens, 0) / 1_000_000) * pricing.input_usd_per_mtok
    output_cost = (max(output_tokens, 0) / 1_000_000) * pricing.output_usd_per_mtok
    return round(input_cost + output_cost, 8)


def extract_usage_tokens(response: Any) -> tuple[int, int]:
    """Return (input_tokens, output_tokens) from an Anthropic response object."""
    usage = getattr(response, "usage", None)
    if not usage:
        return 0, 0
    return int(getattr(usage, "input_tokens", 0) or 0), int(getattr(usage, "output_tokens", 0) or 0)


def safe_error_type(error: BaseException | str | None) -> str | None:
    if error is None:
        return None
    if isinstance(error, str):
        return "".join(ch for ch in error if ch.isalnum() or ch in {"_", "-"})[:80] or "Error"
    return error.__class__.__name__[:80]


def build_usage_event(
    *,
    provider: str,
    model: str,
    request_type: str,
    diagnostic_id: str | None,
    student_id: str | None,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    success: bool,
    error_type: str | None = None,
    created_at: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    safe_input_tokens = max(int(input_tokens or 0), 0)
    safe_output_tokens = max(int(output_tokens or 0), 0)
    safe_latency_ms = max(int(latency_ms or 0), 0)
    total_tokens = safe_input_tokens + safe_output_tokens

    rid = request_id if request_id is not None else get_request_id()

    return {
        "provider": provider,
        "model": model,
        "request_type": request_type,
        "diagnostic_id": diagnostic_id,
        "student_id": student_id,
        "input_tokens": safe_input_tokens,
        "output_tokens": safe_output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": calculate_estimated_cost(
            model=model,
            input_tokens=safe_input_tokens,
            output_tokens=safe_output_tokens,
            provider=provider,
        ),
        "latency_ms": safe_latency_ms,
        "success": bool(success),
        "error_type": None if success else (error_type or "AIError"),
        "created_at": created_at or utc_now_iso(),
        "request_id": rid if rid != "-" else None,
    }


def usage_event_with_context(
    usage_event: dict[str, Any],
    *,
    diagnostic_id: str | None,
    student_id: str | None,
) -> dict[str, Any]:
    event = {k: v for k, v in usage_event.items() if k not in PII_TELEMETRY_KEYS}
    event["diagnostic_id"] = diagnostic_id
    event["student_id"] = student_id
    event["total_tokens"] = int(event.get("input_tokens") or 0) + int(
        event.get("output_tokens") or 0
    )
    if "estimated_cost" not in event:
        event["estimated_cost"] = calculate_estimated_cost(
            model=event.get("model", AI_MODEL),
            input_tokens=int(event.get("input_tokens") or 0),
            output_tokens=int(event.get("output_tokens") or 0),
            provider=event.get("provider", AI_PROVIDER),
        )
    return event


def persist_usage_event(supabase: Any, usage_event: dict[str, Any]) -> bool:
    event = {k: v for k, v in usage_event.items() if k not in PII_TELEMETRY_KEYS}
    try:
        supabase.table("ai_usage_events").insert(event).execute()
    except Exception as primary_error:
        logger.warning(
            "ai_usage_events persistence failed; attempting audit_log fallback",
            extra={
                "error_type": safe_error_type(primary_error),
                "has_diagnostic_id": bool(event.get("diagnostic_id")),
                "has_student_id": bool(event.get("student_id")),
            },
        )
        try:
            supabase.table("audit_log").insert(
                {
                    "diagnostic_id": event.get("diagnostic_id"),
                    "action": "ai_usage_event",
                    "actor": "system",
                    "details": {"telemetry": event},
                    "request_id": event.get("request_id"),
                }
            ).execute()
            return True
        except Exception as fallback_error:
            logger.error(
                "ai_usage_events audit_log fallback failed",
                extra={
                    "primary_error_type": safe_error_type(primary_error),
                    "fallback_error_type": safe_error_type(fallback_error),
                    "has_diagnostic_id": bool(event.get("diagnostic_id")),
                    "has_student_id": bool(event.get("student_id")),
                },
            )
            return False
    # Primary insert succeeded — run alert checks (each catches its own exceptions).
    try:
        check_and_alert_error_rate(supabase)
        check_and_alert_cost(supabase)
    except Exception as alert_exc:
        logger.warning("Alert check failed (non-blocking): %s", alert_exc)
    return True


def parse_event_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def aggregate_monthly_usage(
    events: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    next_month = (
        now.replace(year=now.year + 1, month=1, day=1)
        if now.month == 12
        else now.replace(month=now.month + 1, day=1)
    ).replace(hour=0, minute=0, second=0, microsecond=0)

    current_events = []
    for event in events:
        created_at = parse_event_datetime(event.get("created_at"))
        if created_at is None or month_start <= created_at < next_month:
            current_events.append(event)

    calls = len(current_events)
    successful_calls = sum(1 for event in current_events if event.get("success") is True)
    failed_calls = sum(1 for event in current_events if event.get("success") is False)
    input_tokens = sum(int(event.get("input_tokens") or 0) for event in current_events)
    output_tokens = sum(int(event.get("output_tokens") or 0) for event in current_events)
    total_tokens = sum(int(event.get("total_tokens") or 0) for event in current_events)
    estimated_cost = round(
        sum(float(event.get("estimated_cost") or 0.0) for event in current_events),
        8,
    )
    latency_values = [
        int(event.get("latency_ms") or 0)
        for event in current_events
        if event.get("latency_ms") is not None
    ]
    average_latency = round(sum(latency_values) / len(latency_values), 2) if latency_values else 0

    diagnostic_ids = {
        event.get("diagnostic_id")
        for event in current_events
        if event.get("diagnostic_id") and event.get("success") is True
    }
    diagnostic_count = len(diagnostic_ids) or successful_calls or calls
    average_cost_per_diagnostic = (
        round(estimated_cost / diagnostic_count, 8) if diagnostic_count else 0
    )

    elapsed_days = (
        (now - month_start).total_seconds() / 86_400
    )
    elapsed_days = max(elapsed_days, 1 / 24)
    forecasted_month_end_cost = round((estimated_cost / elapsed_days) * days_in_month, 8)

    by_model: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "provider": "",
            "model": "",
            "calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "latency_values": [],
        }
    )
    for event in current_events:
        key = (event.get("provider") or "unknown", event.get("model") or "unknown")
        bucket = by_model[key]
        bucket["provider"], bucket["model"] = key
        bucket["calls"] += 1
        bucket["successful_calls"] += 1 if event.get("success") is True else 0
        bucket["failed_calls"] += 1 if event.get("success") is False else 0
        bucket["input_tokens"] += int(event.get("input_tokens") or 0)
        bucket["output_tokens"] += int(event.get("output_tokens") or 0)
        bucket["total_tokens"] += int(event.get("total_tokens") or 0)
        bucket["estimated_cost"] += float(event.get("estimated_cost") or 0.0)
        if event.get("latency_ms") is not None:
            bucket["latency_values"].append(int(event.get("latency_ms") or 0))

    model_breakdown = []
    for bucket in by_model.values():
        latency = bucket.pop("latency_values")
        bucket["estimated_cost"] = round(bucket["estimated_cost"], 8)
        bucket["average_latency_ms"] = round(sum(latency) / len(latency), 2) if latency else 0
        model_breakdown.append(bucket)

    return {
        "month_start": month_start.isoformat(),
        "month_end": next_month.isoformat(),
        "current_month_ai_calls": calls,
        "calls": calls,
        "successful_calls": successful_calls,
        "failed_calls": failed_calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": estimated_cost,
        "average_cost_per_diagnostic": average_cost_per_diagnostic,
        "average_latency_ms": average_latency,
        "forecasted_month_end_cost": forecasted_month_end_cost,
        "model_breakdown": sorted(
            model_breakdown,
            key=lambda row: row["estimated_cost"],
            reverse=True,
        ),
    }
