## Features Added Post-MVP

1. **Spanish/English Language Toggle:**  
   The translation system facilitates seamless language switching between Spanish and English, ensuring the landing page, the form, and the results are covered, while some elements of the admin dashboard are pending translation.

2. **PDF Export of Results:** 
   This feature, implemented with jsPDF, allows users to download a comprehensive report that includes overall readiness scores, roadmaps, and key recommendations.

3. **Email Capture Confirmation:** 
   An inline assurance UX has been introduced to the diagnostic form, confirming email capture and enhancing user confidence.

4. **Progress Tracker (UC-03):** 
   The tracker page displays progress through completed steps and employs a progress_token authorization mechanism to ensure security. Completed steps are persisted for convenience.

5. **Production Observability Layer:** 
   This feature tracks AI TCO (Total Cost of Ownership) and introduces an admin authentication token model replacing the previous hardcoded password. New database migrations support production-readiness improvements.

6. **Known Limitations:** 
   - The admin token currently operates as a single shared static value (not user-specific). 
   - The Spanish translation does not cover the admin dashboard. 
   - Cost estimates in the observability layer rely on current Anthropic pricing.

7. **Stripe Test-Mode Paywall (UC-02 / UC-04):**  
   Full matched positions (UC-02) and CV/cover letter generation (UC-04) are now gated behind one-time Stripe Checkout payments (€19 and €15 respectively). The integration runs entirely in **Stripe TEST MODE** — no real transactions occur. Test card `4242 4242 4242 4242` was used for verification.

   Architecture: the FastAPI backend creates a Stripe Checkout Session server-side and returns the hosted checkout URL to the frontend. A webhook endpoint with Stripe signature verification (`stripe.Webhook.construct_event`) listens for `checkout.session.completed` and sets `matches_unlocked` or `documents_unlocked = true` on the relevant `diagnostics` row in Supabase. The frontend reflects the unlocked state on next page load and shows a success banner on return from Stripe. Locked content is represented by blurred placeholder cards (UC-02) or a lock-icon paywall panel (UC-04).

   **Known limitation:** moving to production requires completing Stripe business account verification (bank details, tax registration) and switching from test to live API keys. This was out of scope for the submission timeline. The code and architecture are production-ready; only the Stripe account verification step remains.

