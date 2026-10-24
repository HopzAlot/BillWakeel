"""FastAPI application entrypoint. Run with: uvicorn main:app --reload"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.bills import router as bills_router
from config import settings

app = FastAPI(title="BillWakeel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bills_router)


@app.get("/health")
def health():
    return {"status": "ok"}
