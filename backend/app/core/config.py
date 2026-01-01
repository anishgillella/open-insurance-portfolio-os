"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Open Insurance"
    environment: Literal["development", "staging", "production", "testing"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # API
    api_v1_prefix: str = "/v1"

    # Database (Supabase PostgreSQL)
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/open_insurance",
        description="PostgreSQL connection string (async)",
    )

    # Database pool settings
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    aws_s3_bucket: str = "open-insurance-docs"

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = "insurance-docs"
    pinecone_environment: str = ""

    # AI Services
    mistral_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""

    # Security
    secret_key: str = Field(
        default="change-me-in-production-use-openssl-rand-hex-32",
        description="Secret key for JWT encoding",
    )
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    @computed_field
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @computed_field
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
