from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import diagnostic, admin

app = FastAPI(title="Klar API", version="1.0.0")

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

app.include_router(diagnostic.router, prefix="/api/diagnostic", tags=["diagnostic"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/health")
def health():
    return {"status": "ok", "product": "Klar"}