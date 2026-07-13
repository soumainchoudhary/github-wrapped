"""
Pydantic models for request / response validation.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator
import re


class WrappedRequest(BaseModel):
    """Incoming request body for generating a Wrapped recap."""

    username: str = Field(
        ...,
        min_length=1,
        max_length=39,
        description="GitHub username (letters, digits, hyphens; cannot start/end with hyphen).",
    )
    github_token: Optional[str] = Field(
        default=None,
        description="Optional GitHub PAT with public_repo scope.",
    )
    year: int = Field(
        default=2025,
        ge=2008,
        le=2030,
        description="Calendar year for the recap.",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$", v):
            raise ValueError(
                "Invalid GitHub username. Only alphanumeric characters and "
                "hyphens are allowed (cannot start or end with a hyphen)."
            )
        return v

    @field_validator("github_token")
    @classmethod
    def validate_github_token(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not re.match(r"^[a-zA-Z0-9_\-\.]{20,200}$", v):
            raise ValueError(
                "Invalid GitHub token format. Must be a valid string "
                "between 20 and 200 characters containing alphanumeric characters, "
                "hyphens, dots, or underscores."
            )
        return v


class ContributionDay(BaseModel):
    """A single day on the contribution calendar."""

    date: date
    count: int = Field(ge=0)
    level: int = Field(ge=0, le=4, default=0)


class LanguageBreakdown(BaseModel):
    """Language usage statistics."""

    name: str
    percentage: float = Field(ge=0, le=100)
    bytes: int = Field(ge=0, default=0)
    color: str = Field(default="#8b949e")


class WrappedStats(BaseModel):
    """The full computed Wrapped payload returned to the frontend."""

    username: str
    avatar_url: str = ""
    account_created: Optional[str] = None
    year: int

    # ── Headline numbers ─────────────────────────────────────────
    total_commits: int = 0
    total_stars: int = 0
    total_repos: int = 0
    total_prs: int = 0
    total_issues: int = 0

    # ── Top repo ─────────────────────────────────────────────────
    top_repo_name: str = ""
    top_repo_stars: int = 0
    top_repo_language: str = ""

    # ── Languages ────────────────────────────────────────────────
    languages: list[LanguageBreakdown] = Field(default_factory=list)

    # ── Streaks ──────────────────────────────────────────────────
    longest_streak_days: int = 0
    current_streak_days: int = 0

    # ── Activity patterns ────────────────────────────────────────
    busiest_day_of_week: str = ""
    busiest_month: str = ""
    contributions: list[ContributionDay] = Field(default_factory=list)

    # ── AI personality ───────────────────────────────────────────
    personality: str = ""

    # ── Chrono-type, Coder Mood, and Roast Enhancements ──────────
    hourly_contributions: list[int] = Field(default_factory=lambda: [0]*24)
    chrono_type: str = ""
    coder_mood: str = ""
    mood_roast: str = ""
    recent_commits: list[str] = Field(default_factory=list)

    # ── Phase 2 Developer Utility Enhancements ───────────────────
    recommendations: list[str] = Field(default_factory=list)
    external_contributions_count: int = 0
    top_frameworks: list[str] = Field(default_factory=list)
    markdown_readme: str = ""
