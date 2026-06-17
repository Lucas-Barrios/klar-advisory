from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import stripe
import os
from database import get_supabase

router = APIRouter()

PRODUCTS = {
    "matches": {
        "name": "Matched Positions Unlock",
        "price_eur": 1900,
        "unlock_field": "matches_unlocked",
        "success_path": "matches",
    },
    "documents": {
        "name": "CV & Cover Letter Generation",
        "price_eur": 1500,
        "unlock_field": "documents_unlocked",
        "success_path": "results",
    },
}


class CheckoutRequest(BaseModel):
    diagnostic_id: str
    product: str


@router.post("/create-checkout-session")
def create_checkout_session(body: CheckoutRequest):
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    if body.product not in PRODUCTS:
        raise HTTPException(status_code=400, detail="Invalid product")

    p = PRODUCTS[body.product]
    frontend_url = os.getenv("FRONTEND_URL", "https://klar-advisory.vercel.app")

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
            success_url=f"{frontend_url}/{p['success_path']}/{body.diagnostic_id}?payment=success",
            cancel_url=f"{frontend_url}/{p['success_path']}/{body.diagnostic_id}",
            metadata={"diagnostic_id": body.diagnostic_id, "product": body.product},
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
        metadata = session.get("metadata", {})
        diagnostic_id = metadata.get("diagnostic_id")
        product = metadata.get("product")

        if diagnostic_id and product in PRODUCTS:
            unlock_field = PRODUCTS[product]["unlock_field"]
            supabase = get_supabase()
            supabase.table("diagnostics").update({
                unlock_field: True
            }).eq("id", diagnostic_id).execute()

    return {"status": "ok"}
