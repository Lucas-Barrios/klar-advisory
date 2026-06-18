import logging
import os
from typing import Literal, Optional

import httpx
import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter()

PRODUCTS = {
    "kit": {
        "name": "Germany Application Kit",
        "price_eur": 3900,
        "unlock_fields": ["matches_unlocked", "documents_unlocked"],
        "success_path": "results",
    }
}

_LANG_LABELS = {"en": "English", "es": "Spanish"}


class CheckoutRequest(BaseModel):
    diagnostic_id: str
    product: str
    target_language: Optional[Literal["en", "es"]] = "en"


@router.post("/create-checkout-session")
def create_checkout_session(body: CheckoutRequest):
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    if body.product not in PRODUCTS:
        raise HTTPException(status_code=400, detail="Invalid product")

    p = PRODUCTS[body.product]
    frontend_url = os.getenv("FRONTEND_URL", "https://klar-advisory.vercel.app")

    # {CHECKOUT_SESSION_ID} is a Stripe template literal — it fills it in the redirect URL.
    success_url = (
        f"{frontend_url}/{p['success_path']}/{body.diagnostic_id}"
        f"?payment=success&product={body.product}&session_id={{CHECKOUT_SESSION_ID}}"
    )

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": p["name"]},
                    "unit_amount": p["price_eur"],
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=f"{frontend_url}/{p['success_path']}/{body.diagnostic_id}",
            metadata={
                "diagnostic_id": body.diagnostic_id,
                "product": body.product,
                "target_language": body.target_language or "en",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

    return {"url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # Verify Stripe confirms the payment was actually collected before unlocking.
        if session.payment_status != "paid":
            logger.warning(
                "checkout.session.completed received but payment_status=%s — ignoring",
                session.payment_status,
            )
            return {"status": "ok"}

        # session.metadata may be a StripeObject in newer SDK versions; dict() handles both.
        metadata = dict(session.metadata) if session.metadata else {}
        diagnostic_id = metadata.get("diagnostic_id")
        product = metadata.get("product")
        target_language = metadata.get("target_language", "en")

        if diagnostic_id and product in PRODUCTS:
            supabase = get_supabase()

            # Fetch student name + email via diagnostics→students join.
            student_name = None
            student_email = None
            try:
                diag_row = (
                    supabase.table("diagnostics")
                    .select("students(name, email)")
                    .eq("id", diagnostic_id)
                    .single()
                    .execute()
                )
                student = (diag_row.data or {}).get("students") or {}
                student_name = student.get("name") or "there"
                student_email = student.get("email")
            except Exception:
                logger.warning("Could not fetch student data for diagnostic %s", diagnostic_id)

            # Unlock all fields for this product in a single DB update.
            unlock_payload = {field: True for field in PRODUCTS[product]["unlock_fields"]}
            supabase.table("diagnostics").update(unlock_payload).eq("id", diagnostic_id).execute()

            if product == "kit" and student_email:
                await _send_kit_ready_email(
                    to_email=student_email,
                    name=student_name or "there",
                    diagnostic_id=diagnostic_id,
                    target_language=target_language,
                )

    return {"status": "ok"}


@router.get("/verify-session")
def verify_session(session_id: str):
    """Instant payment-confirmation check called by the frontend on return from Stripe.

    Retrieves the Stripe session, verifies payment_status == "paid", then also
    sets both unlock fields in the database so the page unlocks immediately even
    if the webhook hasn't arrived yet.
    """
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not retrieve session: {e}")

    if session.payment_status != "paid":
        return {"documents_unlocked": False, "matches_unlocked": False, "diagnostic_id": None}

    # session.metadata may be a StripeObject in newer SDK versions; dict() handles both.
    metadata = dict(session.metadata) if session.metadata else {}
    diagnostic_id = metadata.get("diagnostic_id")
    product = metadata.get("product")

    if not diagnostic_id or product not in PRODUCTS:
        return {"documents_unlocked": False, "matches_unlocked": False, "diagnostic_id": diagnostic_id}

    unlock_payload = {field: True for field in PRODUCTS[product]["unlock_fields"]}
    supabase = get_supabase()
    try:
        supabase.table("diagnostics").update(unlock_payload).eq("id", diagnostic_id).execute()
    except Exception:
        logger.warning("verify-session: DB update failed for diagnostic %s", diagnostic_id)

    return {"documents_unlocked": True, "matches_unlocked": True, "diagnostic_id": diagnostic_id}


async def _send_kit_ready_email(
    *,
    to_email: str,
    name: str,
    diagnostic_id: str,
    target_language: str,
) -> None:
    if not to_email or "@" not in to_email:
        logger.warning("Skipping kit email for diagnostic %s — no valid email", diagnostic_id)
        return

    resend_key = os.getenv("RESEND_API_KEY")
    if not resend_key:
        logger.warning("RESEND_API_KEY not set — skipping payment confirmation email")
        return

    from_addr = os.getenv("RESEND_FROM_EMAIL", "noreply@klar-advisory.com")
    frontend_url = os.getenv("FRONTEND_URL", "https://klar-advisory.vercel.app")
    lang_label = _LANG_LABELS.get(target_language, "English")
    cta_url = (
        f"{frontend_url}/results/{diagnostic_id}"
        f"?payment=success&product=kit"
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Your Germany Application Kit is ready</title>
</head>
<body style="margin:0;padding:0;background:#0F1117;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <div style="max-width:600px;margin:0 auto;padding:40px 24px;">

    <div style="margin-bottom:32px;">
      <span style="color:#2563EB;font-size:28px;font-weight:800;letter-spacing:-0.05em;">Klar</span>
    </div>

    <h1 style="color:#F9FAFB;font-size:24px;font-weight:700;margin:0 0 16px;line-height:1.3;">
      Hi {name},
    </h1>

    <p style="color:#9CA3AF;font-size:16px;line-height:1.7;margin:0 0 28px;">
      Payment confirmed. Your <strong style="color:#F9FAFB;">Germany Application Kit</strong> is ready —
      matched positions from Germany's Federal Employment Agency plus a bilingual CV and Cover Letter
      in German and <strong style="color:#F9FAFB;">{lang_label}</strong>.
    </p>

    <a href="{cta_url}"
       style="display:inline-block;background:#2563EB;color:#FFFFFF;padding:14px 32px;
              border-radius:9999px;text-decoration:none;font-weight:700;font-size:15px;
              margin-bottom:36px;">
      Open My Kit →
    </a>

    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:0 0 28px;">

    <p style="color:#6B7280;font-size:13px;line-height:1.7;margin:0 0 24px;">
      Fill in the <span style="color:#F59E0B;font-weight:600;">[bracketed]</span>
      placeholders in your CV and cover letter with your real information before sending to employers.
      Klar generates the structure — you provide the facts.
    </p>

    <p style="color:#4B5563;font-size:12px;margin:0;">
      Klar · Germany Readiness Platform ·
      <a href="{frontend_url}" style="color:#4B5563;text-decoration:underline;">Unsubscribe</a>
    </p>

  </div>
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
                    "to": [to_email],
                    "subject": "Your Germany Application Kit is ready \U0001f389",
                    "html": html,
                },
            )
            if resp.status_code >= 400:
                logger.warning(
                    "Resend returned %s: %s", resp.status_code, resp.text[:200]
                )
    except Exception as exc:
        logger.warning("Failed to send kit-ready email: %s", exc)
