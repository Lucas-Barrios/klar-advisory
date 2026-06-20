import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from routers import diagnostic, admin, payments
from services.rate_limiter import limiter
from services.request_id import RequestIdFilter, set_request_id

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(request_id)s] %(name)s — %(message)s",
)
logging.getLogger().addFilter(RequestIdFilter())

app = FastAPI(title="Klar API", version="1.0.0")
app.state.limiter = limiter


class _RequestIdMiddleware:
    """Pure ASGI middleware: reads/generates X-Request-ID, stores it in contextvar,
    and echoes it back on the response so it's visible in browser devtools."""

    def __init__(self, app):
        self._app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self._app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        request_id = (
            headers.get(b"x-request-id", b"").decode() or str(uuid.uuid4())
        )
        token = set_request_id(request_id)

        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                out_headers = list(message.get("headers", []))
                out_headers.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": out_headers}
            await send(message)

        try:
            await self._app(scope, receive, send_with_request_id)
        finally:
            set_request_id("-")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://klar-advisory.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware must wrap everything, so add it last (outermost layer).
app.add_middleware(_RequestIdMiddleware)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                "You have submitted too many diagnostic requests. "
                "Please wait a while before trying again."
            )
        },
    )

app.include_router(diagnostic.router, prefix="/api/diagnostic", tags=["diagnostic"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])

@app.get("/health")
def health():
    return {"status": "ok", "product": "Klar"}
