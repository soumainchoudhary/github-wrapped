"""
Unit tests for stats_engine.py
"""

from datetime import date, timedelta

import pytest

from backend.app.services.stats_engine import (
    compute_busiest_day,
    compute_busiest_month,
    compute_language_breakdown,
    compute_streaks,
    find_top_repo,
    parse_events_data,
    determine_chrono_type,
    calculate_coder_mood,
    analyze_frameworks_and_tools,
    audit_habits_and_hygiene,
    calculate_external_contributions,
    generate_markdown_readme,
    build_wrapped_stats,
)


# ── Language breakdown ───────────────────────────────────────────────────────

class TestLanguageBreakdown:
    def test_empty_input(self):
        result = compute_language_breakdown({})
        assert result == []

    def test_single_language(self):
        result = compute_language_breakdown({"Python": 10000})
        assert len(result) == 1
        assert result[0].name == "Python"
        assert result[0].percentage == 100.0

    def test_top_n_with_other(self):
        langs = {
            "Python": 500,
            "JavaScript": 300,
            "TypeScript": 200,
            "Go": 150,
            "Rust": 100,
            "Ruby": 50,     # should go into "Other"
            "Dart": 30,     # should go into "Other"
        }
        result = compute_language_breakdown(langs, top_n=5)
        names = [r.name for r in result]
        assert "Python" in names
        assert "Other" in names
        assert len(result) == 6  # 5 + Other

    def test_percentages_sum_to_100(self):
        langs = {"Python": 700, "JS": 200, "Go": 100}
        result = compute_language_breakdown(langs, top_n=5)
        total = sum(r.percentage for r in result)
        assert abs(total - 100.0) < 0.5  # rounding tolerance

    def test_respects_top_n(self):
        langs = {f"Lang{i}": 100 - i for i in range(10)}
        result = compute_language_breakdown(langs, top_n=3)
        # 3 top + 1 Other
        assert len(result) == 4


# ── Streaks ──────────────────────────────────────────────────────────────────

class TestStreaks:
    def test_empty_days(self):
        longest, current = compute_streaks([])
        assert longest == 0
        assert current == 0

    def test_all_zeros(self):
        days = [{"date": date(2025, 1, d), "count": 0} for d in range(1, 8)]
        longest, current = compute_streaks(days)
        assert longest == 0
        assert current == 0

    def test_continuous_streak(self):
        days = [{"date": date(2025, 1, d), "count": d} for d in range(1, 11)]
        longest, current = compute_streaks(days)
        assert longest == 10
        assert current == 10

    def test_broken_streak(self):
        days = [
            {"date": date(2025, 1, 1), "count": 5},
            {"date": date(2025, 1, 2), "count": 3},
            {"date": date(2025, 1, 3), "count": 0},  # break
            {"date": date(2025, 1, 4), "count": 1},
            {"date": date(2025, 1, 5), "count": 2},
            {"date": date(2025, 1, 6), "count": 4},
        ]
        longest, current = compute_streaks(days)
        assert longest == 3  # days 4-6
        assert current == 3  # still going at end

    def test_streak_ending_with_zero(self):
        days = [
            {"date": date(2025, 1, 1), "count": 1},
            {"date": date(2025, 1, 2), "count": 2},
            {"date": date(2025, 1, 3), "count": 0},
        ]
        longest, current = compute_streaks(days)
        assert longest == 2
        assert current == 0


# ── Busiest day ──────────────────────────────────────────────────────────────

class TestBusiestDay:
    def test_empty(self):
        assert compute_busiest_day([]) == "N/A"

    def test_returns_weekday_name(self):
        # 2025-01-06 is a Monday
        days = [
            {"date": date(2025, 1, 6), "count": 10},  # Monday
            {"date": date(2025, 1, 7), "count": 5},   # Tuesday
        ]
        result = compute_busiest_day(days)
        assert result == "Monday"


# ── Busiest month ────────────────────────────────────────────────────────────

class TestBusiestMonth:
    def test_empty(self):
        assert compute_busiest_month([]) == "N/A"

    def test_returns_month_name(self):
        days = [
            {"date": date(2025, 3, 1), "count": 20},
            {"date": date(2025, 7, 1), "count": 5},
        ]
        result = compute_busiest_month(days)
        assert result == "March"


# ── Top repo ─────────────────────────────────────────────────────────────────

class TestTopRepo:
    def test_empty(self):
        name, stars, lang = find_top_repo([])
        assert name == ""
        assert stars == 0

    def test_picks_most_starred(self):
        repos = [
            {"name": "a", "stargazers_count": 10, "language": "Python"},
            {"name": "b", "stargazers_count": 50, "language": "Go"},
            {"name": "c", "stargazers_count": 5, "language": "Rust"},
        ]
        name, stars, lang = find_top_repo(repos)
        assert name == "b"
        assert stars == 50
        assert lang == "Go"


# ── Chrono-type and Mood Enhancements ────────────────────────────────────────

class TestChronoTypeAndMood:
    def test_determine_chrono_type(self):
        # Empty hourly contributions should return Daylight Dev
        assert determine_chrono_type([0]*24) == "Daylight Dev ☀️"

        # Busiest at 2 AM (gremlin)
        hourly_gremlin = [0]*24
        hourly_gremlin[2] = 10
        assert determine_chrono_type(hourly_gremlin) == "Midnight Gremlin 😈"

        # Busiest at 8 AM (early bird)
        hourly_early = [0]*24
        hourly_early[8] = 5
        assert determine_chrono_type(hourly_early) == "Early Bird 🌅"

        # Busiest at 3 PM (afternoon architect)
        hourly_afternoon = [0]*24
        hourly_afternoon[15] = 12
        assert determine_chrono_type(hourly_afternoon) == "Afternoon Architect 🏗️"

        # Busiest at 9 PM (night owl)
        hourly_night = [0]*24
        hourly_night[21] = 8
        assert determine_chrono_type(hourly_night) == "Night Owl 🦉"

    def test_calculate_coder_mood(self):
        # Empty commit messages
        assert calculate_coder_mood([]) == "Zen Architect 🧘"

        # Zen keywords match
        assert calculate_coder_mood(["feat: add user login", "docs: update readme"]) == "Zen Architect 🧘"

        # Chaotic keywords / short message matches
        assert calculate_coder_mood(["wip", "update code", "run sync"]) == "Chaotic Hacker ⚡"

        # Frustrated keywords matches
        assert calculate_coder_mood(["fix annoying bug", "wtf this crashed again"]) == "Frustrated Solver 🤯"

        # Exhausted keywords matches
        assert calculate_coder_mood(["so tired done with this", "finally finished sigh"]) == "Exhausted Warrior 😴"

    def test_parse_events_data(self):
        dummy_events = [
            {
                "type": "PushEvent",
                "created_at": "2026-06-21T02:15:00Z",
                "payload": {
                    "commits": [
                        {"message": "feat: clean start"},
                        {"message": "wip progress"}
                    ]
                }
            },
            {
                "type": "PushEvent",
                "created_at": "2026-06-21T15:30:00Z",
                "payload": {
                    "commits": [
                        {"message": "fix: crash bug"}
                    ]
                }
            },
            {
                "type": "WatchEvent", # should be ignored
                "created_at": "2026-06-21T18:00:00Z",
                "payload": {}
            }
        ]

        hourly, messages = parse_events_data(dummy_events)
        
        # Check hourly bins (hour 2 has 2 commits, hour 15 has 1 commit)
        assert hourly[2] == 2
        assert hourly[15] == 1
        assert sum(hourly) == 3
        
        # Check messages extracted uniquely
        assert "feat: clean start" in messages
        assert "wip progress" in messages
        assert "fix: crash bug" in messages
        assert len(messages) == 3


# ── Developer Utility Enhancements (Phase 2) ───────────────────────────────

class TestDeveloperUtilityEnhancements:
    def test_analyze_frameworks_and_tools(self):
        repos = [
            {"topics": ["react", "frontend"], "description": "A python app with fastapi backend"},
            {"topics": ["docker"], "description": "Just kubernetes deployment scripts"},
            {"topics": ["django", "reactjs"], "description": "Old legacy express project"},
        ]
        frameworks = analyze_frameworks_and_tools(repos)
        # Fastapi should match from description, react/docker/django/reactjs/express/kubernetes from topics/descriptions
        assert len(frameworks) <= 5
        assert "React" in frameworks
        assert "FastAPI" in frameworks
        assert "Docker" in frameworks

    def test_audit_habits_and_hygiene(self):
        # Top repo missing license & description + chaotic mood
        repos = [
            {"name": "messy-repo", "stargazers_count": 10, "fork": False, "license": None, "description": None}
        ]
        recs = audit_habits_and_hygiene(repos, "Chaotic Hacker ⚡", total_prs=0, total_commits=100)
        assert len(recs) == 3
        # Should recommend adding license, description, and using conventional commits or PRs
        assert any("LICENSE" in r for r in recs)
        assert any("description" in r for r in recs)
        assert any("Conventional" in r for r in recs)

    def test_calculate_external_contributions(self):
        events = [
            {"repo": {"name": "other-user/cool-lib"}},
            {"repo": {"name": "my-user/my-repo"}},
            {"repo": {"name": "another-org/project"}},
        ]
        count = calculate_external_contributions(events, "my-user")
        assert count == 2

    def test_generate_markdown_readme(self):
        from backend.app.models.schemas import WrappedStats, LanguageBreakdown
        stats = WrappedStats(
            username="test-user",
            year=2025,
            total_commits=150,
            total_stars=12,
            total_repos=5,
            longest_streak_days=10,
            chrono_type="Early Bird 🌅",
            coder_mood="Zen Architect 🧘",
            personality="A balanced developer.",
            top_frameworks=["FastAPI", "React"],
            languages=[
                LanguageBreakdown(name="Python", percentage=80.0, bytes=800, color="#fff"),
                LanguageBreakdown(name="TypeScript", percentage=20.0, bytes=200, color="#000"),
            ]
        )
        readme = generate_markdown_readme(stats)
        assert "### 🎁 My GitHub Wrapped 2025" in readme
        assert "**Total Commits** | 150" in readme
        assert "**Top Languages** | Python, TypeScript" in readme
        assert "**Frameworks Used** | FastAPI, React" in readme
        assert "Zen Architect 🧘" in readme

    def test_build_wrapped_stats_integration(self):
        profile = {"avatar_url": "https://avatar.url", "created_at": "2020-01-01"}
        repos = [
            {"name": "project1", "stargazers_count": 5, "topics": ["fastapi", "react"], "license": {"key": "mit"}, "description": "Cool app"}
        ]
        lang_bytes = {"Python": 1000}
        contrib_days = [{"date": date(2025, 1, 1), "count": 5, "level": 1}]
        events = [
            {
                "type": "PushEvent",
                "created_at": "2026-06-21T08:15:00Z",
                "repo": {"name": "test-coder/project1"},
                "payload": {"commits": [{"message": "feat: init project"}]}
            },
            {
                "type": "PushEvent",
                "created_at": "2026-06-21T09:30:00Z",
                "repo": {"name": "test-coder/project1"},
                "payload": {"commits": [{"message": "fix: compile error"}]}
            }
        ]
        
        stats = build_wrapped_stats(
            username="test-coder",
            profile=profile,
            repos=repos,
            lang_bytes=lang_bytes,
            contribution_days=contrib_days,
            contribution_collection=None,
            year=2025,
            personality="An AI Summary",
            events=events
        )
        
        assert stats.username == "test-coder"
        assert stats.external_contributions_count == 0
        assert "FastAPI" in stats.top_frameworks
        assert len(stats.recommendations) > 0
        assert "My GitHub Wrapped 2025" in stats.markdown_readme
