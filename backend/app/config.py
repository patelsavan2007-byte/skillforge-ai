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
    RESUME_NER_MODEL: str = "oksomu/resume-ner"
    RESUME_NER_MIN_CONFIDENCE: float = 0.60

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
