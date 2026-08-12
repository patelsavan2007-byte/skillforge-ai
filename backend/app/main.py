from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database.mongodb import connect_to_mongodb, close_mongodb_connection

from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.resumes import router as resumes_router
from app.routes.portfolios import router as portfolios_router
from app.routes.career_profiles import router as career_profiles_router
from app.routes.learning_paths import router as learning_paths_router
from app.routes.progress import router as progress_router

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

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
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

# Register routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(resumes_router)
app.include_router(portfolios_router)
app.include_router(career_profiles_router)
app.include_router(learning_paths_router)
app.include_router(progress_router)

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "SkillForge AI backend is running"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Backend is running"
    }

@app.get("/api/health", tags=["health"])
async def health_check():
    return {
        "status": "ok",
        "service": "skillforge-ai-api",
        "database": "mongodb_atlas",
    }

