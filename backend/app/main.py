"""
app/main.py
───────────
FastAPI application entry point.

This file is intentionally minimal. Its only jobs are:
  1. Create the FastAPI app instance
  2. Configure CORS middleware
  3. Register routers (one per phase)
  4. Expose a health-check endpoint
  5. Handle startup/shutdown lifecycle events

We use the `lifespan` context manager (FastAPI 0.93+) instead of the
deprecated `@app.on_event("startup")` pattern.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


# ── Lifespan ───────────────────────────────────────────────────────────────────
# Code before `yield` runs on startup; code after runs on shutdown.
# We'll add database connection checks and Celery startup here in later phases.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"🎵 {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    print(f"   Environment : {settings.ENVIRONMENT}")
    print(f"   Debug mode  : {settings.DEBUG}")
    yield
    # Shutdown
    print(f"🛑 {settings.APP_NAME} shutting down...")


# ── App Instance ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Moodify AI — automatically creates Spotify playlists "
        "based on your listening history and mood."
    ),
    # OpenAPI docs are available at /docs (Swagger) and /redoc
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── CORS Middleware ─────────────────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) allows our React frontend (port 3000)
# to make API calls to our FastAPI backend (port 8000).
# Without this, the browser blocks the request.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,   # Required for cookies / auth headers
    allow_methods=["*"],      # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],      # Allow Authorization, Content-Type, etc.
)


# ── Routes ─────────────────────────────────────────────────────────────────────
from app.api.auth import router as auth_router
from app.api.tracks import router as tracks_router

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(tracks_router, prefix="/api/tracks", tags=["tracks"])


# ── Health Check ───────────────────────────────────────────────────────────────
# A simple endpoint that confirms the API is alive.
# Used by Docker health checks and load balancers.
@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["system"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
    }
