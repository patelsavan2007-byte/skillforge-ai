from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import re

from app.config import settings
from app.database.mongodb import connect_to_mongodb, close_mongodb_connection

from app.routes.auth import router as auth_router, google_login, google_callback
from app.routes.users import router as users_router
from app.routes.resumes import router as resumes_router
from app.routes.portfolios import router as portfolios_router
from app.routes.career_profiles import router as career_profiles_router
from app.routes.learning_paths import router as learning_paths_router
from app.routes.progress import router as progress_router
from fastapi import APIRouter

# Alias router for Google OAuth when configured without /api prefix
auth_alias_router = APIRouter(prefix="/auth", tags=["auth-alias"])
auth_alias_router.add_api_route("/google/login", google_login, methods=["GET"])
auth_alias_router.add_api_route("/google/callback", google_callback, methods=["GET"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MongoDB connection and indexes
    connect_to_mongodb()
    
    yield
    
    # Close MongoDB connection gracefully on shutdown
    close_mongodb_connection()

app = FastAPI(
    title="SkillForge AI API",
    description="Backend service with PyMongo MongoDB Atlas integration",
    version="2.0.0",
    lifespan=lifespan,
)

# Session middleware configuration
is_production = settings.ENVIRONMENT.lower() == "production"
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    session_cookie="skillforge_session",
    max_age=14 * 24 * 3600,
    same_site="none" if is_production else "lax",
    https_only=is_production,
)

@app.middleware("http")
async def normalize_path_middleware(request: Request, call_next):
    # Normalize consecutive slashes in request path (e.g. //api/auth/me -> /api/auth/me)
    if "//" in request.scope.get("path", ""):
        request.scope["path"] = re.sub(r"/+", "/", request.scope["path"])
    return await call_next(request)

# CORS middleware MUST be added outermost (last in Starlette) so preflight OPTIONS and error responses return CORS headers cleanly
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app|.*\.onrender\.com)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(auth_alias_router)
app.include_router(users_router)
app.include_router(resumes_router)
app.include_router(resumes_router, prefix="/api/resume", tags=["resume-alias"])
app.include_router(portfolios_router)
app.include_router(career_profiles_router)
app.include_router(learning_paths_router)
app.include_router(progress_router)

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "SkillForge AI backend is running",
        "low_memory_mode": getattr(settings, "LOW_MEMORY_MODE", False),
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Backend is running",
        "low_memory_mode": getattr(settings, "LOW_MEMORY_MODE", False),
    }

@app.get("/api/health", tags=["health"])
async def health_check():
    return {
        "status": "ok",
        "service": "skillforge-ai-api",
        "database": "mongodb_atlas",
        "low_memory_mode": getattr(settings, "LOW_MEMORY_MODE", False),
        "enable_heavy_models": getattr(settings, "ENABLE_HEAVY_MODELS", True),
    }

