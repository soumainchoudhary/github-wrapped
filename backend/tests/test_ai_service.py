"""
Unit tests for ai_service.py — focuses on the fallback logic.
"""

import pytest

from backend.app.models.schemas import LanguageBreakdown, WrappedStats
from backend.app.services.ai_service import generate_personality_fallback


def _make_stats(**overrides) -> WrappedStats:
    """Helper to create WrappedStats with sensible defaults + overrides."""
    defaults = {
        "username": "testuser",
        "year": 2025,
        "total_commits": 100,
        "total_stars": 10,
        "total_repos": 5,
        "total_prs": 3,
        "total_issues": 2,
        "longest_streak_days": 5,
        "current_streak_days": 2,
        "busiest_day_of_week": "Monday",
        "busiest_month": "March",
        "languages": [
            LanguageBreakdown(name="Python", percentage=60.0, bytes=6000, color="#3572A5"),
            LanguageBreakdown(name="Go", percentage=30.0, bytes=3000, color="#00ADD8"),
        ],
    }
    defaults.update(overrides)
    return WrappedStats(**defaults)


class TestFallbackPersonality:
    def test_returns_non_empty_string(self):
        stats = _make_stats()
        result = generate_personality_fallback(stats)
        assert isinstance(result, str)
        assert len(result) > 10

    def test_marathon_coder_archetype(self):
        stats = _make_stats(longest_streak_days=45)
        result = generate_personality_fallback(stats)
        assert "45" in result or "streak" in result.lower() or "marathon" in result.lower()

    def test_polyglot_archetype(self):
        stats = _make_stats(
            languages=[
                LanguageBreakdown(name=f"Lang{i}", percentage=20.0)
                for i in range(5)
            ]
        )
        result = generate_personality_fallback(stats)
        assert "5" in result or "polyglot" in result.lower() or "language" in result.lower()

    def test_star_collector_archetype(self):
        stats = _make_stats(total_stars=100)
        result = generate_personality_fallback(stats)
        assert "100" in result or "star" in result.lower()

    def test_weekend_warrior_archetype(self):
        stats = _make_stats(
            busiest_day_of_week="Saturday",
            longest_streak_days=1,  # avoid marathon trigger
            total_stars=0,          # avoid star trigger
        )
        stats.languages = [LanguageBreakdown(name="Python", percentage=100.0)]
        result = generate_personality_fallback(stats)
        assert "saturday" in result.lower() or "weekend" in result.lower()

    def test_generic_fallback(self):
        """Stats that don't match any archetype should still return something."""
        stats = _make_stats(
            longest_streak_days=1,
            total_stars=0,
            total_commits=50,
            busiest_day_of_week="Wednesday",
        )
        stats.languages = [LanguageBreakdown(name="Python", percentage=100.0)]
        result = generate_personality_fallback(stats)
        assert len(result) > 10
        assert "Python" in result or "50" in result
