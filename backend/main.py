"""BillWakeel — FastAPI application entry point.

Run from the ``backend/`` directory:
    uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.bills import router as bills_router

app = FastAPI(
    title="BillWakeel API",
    description="Utility bill verification platform for Pakistan.",
    version="0.1.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────
app.include_router(bills_router)


# ── Health check ─────────────────────────────────────────────────────────
@app.get("/health", summary="Liveness check")
def health():
    """Return ``{"status": "ok"}`` so monitoring and the frontend can
    verify the API is running."""
    return {"status": "ok"}
