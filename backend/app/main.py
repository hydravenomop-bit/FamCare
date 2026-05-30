"""
FamCARE Multi-Service Bulk Scheduler — FastAPI Application.

Main entry point. Configures CORS, registers routes, and seeds the
database on first startup.

Run with: uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables, async_session_factory
from app.api.router import router
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan — runs on startup and shutdown.

    On startup:
    1. Create database tables (idempotent)
    2. Seed with sample data if tables are empty
    """
    await create_tables()

    async with async_session_factory() as session:
        await seed_database(session)

    yield  # Application runs here



app = FastAPI(
    title="FamCARE Multi-Service Bulk Scheduler",
    description=(
        "Booking engine for a home healthcare platform. "
        "Patients book multiple services across multiple days in a single "
        "atomic checkout. Supports conflict detection using full service "
        "duration for both caregiver and patient overlaps."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "famcare-scheduler"}
