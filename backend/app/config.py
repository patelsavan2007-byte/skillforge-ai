import os
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(BACKEND_DIR, ".env")

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:5173"
    SESSION_SECRET: str = "skillforge_ai_super_secret_session_key_2026_x89q"
    MONGODB_URI: str = ""
    MONGODB_DATABASE: str = "skillforge"
    ENVIRONMENT: str = "development"
    ALLOW_MONGOMOCK: bool = False
    RESUME_NER_MODEL: str = "oksomu/resume-ner"
    RESUME_NER_MIN_CONFIDENCE: float = 0.60
    GEMINI_API_KEY: str = ""
    # Stage 3 only: local persistent semantic-course index.  It is separate
    # from MongoDB, which remains the Stage 5 system of record.
    CHROMADB_DIR: str = os.path.join(BACKEND_DIR, "app", "data", "chroma_db")
    CHROMA_COLLECTION_NAME: str = "skillforge_courses"

    # Memory optimization settings for Render Free / constrained hosting
    LOW_MEMORY_MODE: bool = (
        os.getenv("LOW_MEMORY_MODE", "").lower() in ("true", "1")
        or os.getenv("RENDER", "").lower() in ("true", "1")
        or bool(os.getenv("RENDER_SERVICE_ID"))
    )
    ENABLE_HEAVY_MODELS: bool = (
        os.getenv("ENABLE_HEAVY_MODELS", "").lower() in ("true", "1")
        if "ENABLE_HEAVY_MODELS" in os.environ
        else not (
            os.getenv("LOW_MEMORY_MODE", "").lower() in ("true", "1")
            or os.getenv("RENDER", "").lower() in ("true", "1")
            or bool(os.getenv("RENDER_SERVICE_ID"))
        )
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Startup diagnostics — never log actual secrets
def _log_config_status():
    print(f"[Config] .env file path: {ENV_FILE_PATH}")
    print(f"[Config] .env file exists: {os.path.exists(ENV_FILE_PATH)}")
    print(f"[Config] GOOGLE_CLIENT_ID loaded: {'YES (' + settings.GOOGLE_CLIENT_ID[:12] + '...)' if settings.GOOGLE_CLIENT_ID else 'NO (empty)'}")
    print(f"[Config] GOOGLE_CLIENT_SECRET loaded: {'YES' if settings.GOOGLE_CLIENT_SECRET else 'NO (empty)'}")
    print(f"[Config] GOOGLE_REDIRECT_URI: {settings.GOOGLE_REDIRECT_URI}")
    print(f"[Config] FRONTEND_URL: {settings.FRONTEND_URL}")
    print(f"[Config] ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"[Config] MONGODB_DATABASE: {settings.MONGODB_DATABASE}")
    print(f"[Config] GEMINI_API_KEY loaded: {'YES' if settings.GEMINI_API_KEY else 'NO (empty)'}")
    print(f"[Config] LOW_MEMORY_MODE: {settings.LOW_MEMORY_MODE}")
    print(f"[Config] ENABLE_HEAVY_MODELS: {settings.ENABLE_HEAVY_MODELS}")

_log_config_status()
