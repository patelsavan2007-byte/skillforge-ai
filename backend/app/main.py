from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import init_db
from app.routes.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="SkillForge AI Auth API",
    description="Backend service strictly for Google OAuth authentication",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware configuration
is_production = settings.ENVIRONMENT.lower() == "production"
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    session_cookie="skillforge_session",
    max_age=14 * 24 * 3600,
    same_site="lax",
    https_only=is_production,
)

app.include_router(auth_router)

@app.get("/api/health", tags=["health"])
async def health_check():
    return {
        "status": "ok",
        "service": "skillforge-ai-auth",
    }
