from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All secrets are read strictly from the environment / .env — no hardcoded fallbacks.

    If JWT_SECRET_KEY or FERNET_KEY is missing the app refuses to start with a clear error.
    Run `python generate_env.py` in /backend to create a .env with fresh secrets.
    """

    # App
    PROJECT_NAME: str = "OmniHealth Graph"
    API_V1_STR: str = "/api"

    # Security (REQUIRED, no defaults)
    JWT_SECRET_KEY: str
    FERNET_KEY: str  # urlsafe-base64 32-byte key (Fernet.generate_key())
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # MongoDB (falls back to an embedded in-memory store if unreachable)
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "healthcare_optimization"

    # FalkorDB (the load-bearing graph layer)
    FALKORDB_HOST: str = "localhost"
    FALKORDB_PORT: int = 6379
    FALKORDB_PASSWORD: Optional[str] = None

    # Gemini (optional: simulated LLM is used when empty)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_ORIGIN_REGEX: str = r"https://.*\.vercel\.app"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), extra="ignore", case_sensitive=True
    )

    # Backwards-compatible alias used by security.py
    @property
    def SECRET_KEY(self) -> str:
        return self.JWT_SECRET_KEY


settings = Settings()
