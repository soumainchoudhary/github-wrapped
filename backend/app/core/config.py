"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration for GitHub Wrapped backend."""

    # ── HuggingFace (optional) ──────────────────────────────────────────
    hf_api_token: str = Field(
        default="",
        description="HuggingFace API token for AI personality summaries.",
    )
    hf_model_id: str = Field(
        default="Qwen/Qwen2.5-7B-Instruct",
        description="HuggingFace model to query for personality text.",
    )
    hf_timeout_seconds: float = Field(
        default=3.0,
        description="Maximum seconds to wait for the HF API response.",
    )

    # ── Server ──────────────────────────────────────────────────────────
    production: bool = Field(
        default=False,
        description="Enable production mode to disable developer endpoints/tools.",
    )
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    allowed_origins: str = Field(
        default="http://localhost:8501",
        description="Comma-separated CORS origins.",
    )

    # ── Rate-limiting ───────────────────────────────────────────────────
    rate_limit: str = Field(
        default="30/minute",
        description="Default rate limit applied to API endpoints.",
    )

    # ── Cache ───────────────────────────────────────────────────────────
    cache_ttl_seconds: int = Field(
        default=300,
        description="Time-to-live (seconds) for in-memory cached responses.",
    )
    cache_max_size: int = Field(
        default=256,
        description="Maximum number of entries in the in-memory cache.",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton instance
settings = Settings()
