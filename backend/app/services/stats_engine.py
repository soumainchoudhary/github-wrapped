"""
Stats engine — crunches raw GitHub data into WrappedStats.

Works on:
  • The list of repos (REST API payload)
  • The contribution calendar days (GraphQL / synthetic)
  • Aggregated language bytes
"""

from __future__ import annotations

import calendar
from collections import Counter
from typing import Any, Optional

from backend.app.models.schemas import (
    ContributionDay,
    LanguageBreakdown,
    WrappedStats,
)
from backend.app.services.github_service import LANG_COLORS


def compute_language_breakdown(
    lang_bytes: dict[str, int],
    top_n: int = 5,
) -> list[LanguageBreakdown]:
    """
    Convert raw {lang: bytes} into a sorted top-N list with percentages.
    Languages outside top_n are grouped into "Other".
    """
    total = sum(lang_bytes.values()) or 1
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)

    result: list[LanguageBreakdown] = []
    other_bytes = 0

    for i, (lang, byte_count) in enumerate(sorted_langs):
        if i < top_n:
            result.append(
                LanguageBreakdown(
                    name=lang,
                    percentage=round(byte_count / total * 100, 1),
                    bytes=byte_count,
                    color=LANG_COLORS.get(lang, "#8b949e"),
                )
            )
        else:
            other_bytes += byte_count

    if other_bytes:
        result.append(
            LanguageBreakdown(
                name="Other",
                percentage=round(other_bytes / total * 100, 1),
                bytes=other_bytes,
                color="#8b949e",
            )
        )

    return result


def compute_streaks(
    days: list[dict[str, Any]],
) -> tuple[int, int]:
    """
    Return (longest_streak, current_streak) from a sorted list of
    contribution days [{date, count, ...}].
    """
    if not days:
        return 0, 0

    sorted_days = sorted(days, key=lambda d: d["date"])

    longest = 0
    current = 0

    for day in sorted_days:
        if day["count"] > 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    # Recalculate current streak from the end
    current_streak = 0
    for day in reversed(sorted_days):
        if day["count"] > 0:
            current_streak += 1
        else:
            break

    return longest, current_streak


def compute_busiest_day(
    days: list[dict[str, Any]],
) -> str:
    """Return the day-of-week name with the most total contributions."""
    if not days:
        return "N/A"

    weekday_totals: Counter = Counter()
    for day in days:
        weekday_totals[day["date"].strftime("%A")] += day["count"]

    if not weekday_totals:
        return "N/A"

    return weekday_totals.most_common(1)[0][0]


def compute_busiest_month(
    days: list[dict[str, Any]],
) -> str:
    """Return the month name with the most total contributions."""
    if not days:
        return "N/A"

    month_totals: Counter = Counter()
    for day in days:
        month_totals[calendar.month_name[day["date"].month]] += day["count"]

    if not month_totals:
        return "N/A"

    return month_totals.most_common(1)[0][0]


def find_top_repo(
    repos: list[dict[str, Any]],
) -> tuple[str, int, str]:
    """
    Find the user's most-starred repo.
    Returns (name, stars, primary_language).
    """
    if not repos:
        return "", 0, ""

    top = max(repos, key=lambda r: r.get("stargazers_count", 0))
    return (
        top.get("name", ""),
        top.get("stargazers_count", 0),
        top.get("language") or "",
    )


def parse_events_data(
    events: list[dict[str, Any]]
) -> tuple[list[int], list[str]]:
    """
    Extract hourly commit distribution and commit messages from PushEvents.
    Returns (hourly_contributions, list_of_commit_messages).
    """
    hourly_contributions = [0] * 24
    commit_messages: list[str] = []

    for event in events:
        if event.get("type") != "PushEvent":
            continue

        # Extract hour from "created_at" (format: YYYY-MM-DDTHH:MM:SSZ)
        created_at = event.get("created_at", "")
        if len(created_at) >= 13:
            try:
                hour_str = created_at[11:13]
                hour = int(hour_str)
                if 0 <= hour < 24:
                    commits_count = len(event.get("payload", {}).get("commits", [])) or 1
                    hourly_contributions[hour] += commits_count
            except ValueError:
                pass

        # Extract commit messages
        commits = event.get("payload", {}).get("commits", [])
        for commit in commits:
            msg = commit.get("message", "").strip()
            if msg and msg not in commit_messages:
                commit_messages.append(msg)

    return hourly_contributions, commit_messages[:50]


def determine_chrono_type(hourly_bins: list[int]) -> str:
    """
    Determine the developer's chrono-type based on the hour bins (0-23 UTC).
    Buckets:
      - Midnight Gremlin 😈: 00:00 - 06:00
      - Early Bird 🌅: 06:00 - 12:00
      - Afternoon Architect 🏗️: 12:00 - 18:00
      - Night Owl 🦉: 18:00 - 00:00
    """
    if sum(hourly_bins) == 0:
        return "Daylight Dev ☀️"

    gremlin = sum(hourly_bins[0:6])
    early = sum(hourly_bins[6:12])
    afternoon = sum(hourly_bins[12:18])
    night = sum(hourly_bins[18:24])

    counts = {
        "Midnight Gremlin 😈": gremlin,
        "Early Bird 🌅": early,
        "Afternoon Architect 🏗️": afternoon,
        "Night Owl 🦉": night,
    }
    return max(counts.items(), key=lambda x: x[1])[0]


def calculate_coder_mood(commits: list[str]) -> str:
    """
    Categorize developer's coding vibe based on keywords in commit messages.
    """
    if not commits:
        return "Zen Architect 🧘"

    chaotic_count = 0.0
    frustrated_count = 0.0
    zen_count = 0.0
    low_energy_count = 0.0

    chaotic_keywords = ["test", "update", "temp", "wip", "work", "stuff", "code", "run", "make", "sync"]
    frustrated_keywords = ["fix", "error", "bug", "failed", "broken", "issue", "wrong", "crash", "wtf", "please", "hope", "hate", "crying", "help"]
    zen_keywords = ["feat", "docs", "refactor", "style", "clean", "test:", "chore", "merge", "implement", "add", "remove"]
    low_energy_keywords = ["tired", "sleep", "done", "meh", "whatever", "finally", "sigh", "slow"]

    for msg in commits:
        msg_lower = msg.lower()
        if msg.isupper() and len(msg) > 4:
            chaotic_count += 2.0
        if any(kw in msg_lower for kw in frustrated_keywords):
            frustrated_count += 1.5
        elif any(kw in msg_lower for kw in zen_keywords):
            zen_count += 1.0
        elif any(kw in msg_lower for kw in chaotic_keywords) or len(msg) < 8:
            chaotic_count += 1.0
        if any(kw in msg_lower for kw in low_energy_keywords):
            low_energy_count += 1.0

    scores = {
        "Zen Architect 🧘": zen_count,
        "Chaotic Hacker ⚡": chaotic_count,
        "Frustrated Solver 🤯": frustrated_count,
        "Exhausted Warrior 😴": low_energy_count,
    }

    if max(scores.values()) == 0.0:
        return "Zen Architect 🧘"
    return max(scores.items(), key=lambda x: x[1])[0]


def generate_fallback_roast(coder_mood: str) -> str:
    """Provide a witty fallback roast based on the developer's Coder Mood."""
    clean_mood = coder_mood.split(" ")[0] if " " in coder_mood else coder_mood
    roasts = {
        "Zen": (
            "Your commit messages are so clean and structured it feels like they were written "
            "by a polite robotic butler. Do you ever let loose and scream into the void?"
        ),
        "Chaotic": (
            "Your commit history reads like an existential crisis. 'wip', 'update', 'test'—"
            "are you writing code, or just poking it with a stick to see if it responds?"
        ),
        "Frustrated": (
            "The sheer volume of 'fixes' and bug references suggests you spend 90% of your time "
            "fighting your own creations. Remember, coding is the art of debugging your own thoughts."
        ),
        "Exhausted": (
            "You sound like you need a 3-month nap. Your code seems to be fueled entirely by "
            "late-night caffeine, deep sighs, and the immediate desire to close your laptop."
        ),
    }
    return roasts.get(clean_mood, "An intriguing developer with a coding signature that defies standard analysis.")


def analyze_frameworks_and_tools(repos: list[dict[str, Any]]) -> list[str]:
    """Scan repository topics and descriptions to aggregate framework usage."""
    frameworks_tooling = {
        "React": ["react", "reactjs"],
        "Vue": ["vue", "vuejs"],
        "Angular": ["angular", "angularjs"],
        "Next.js": ["nextjs", "next.js"],
        "FastAPI": ["fastapi"],
        "Django": ["django"],
        "Flask": ["flask"],
        "Express": ["express", "expressjs"],
        "Spring Boot": ["spring-boot", "springboot"],
        "Laravel": ["laravel"],
        "Ruby on Rails": ["rails", "ruby-on-rails"],
        "TensorFlow": ["tensorflow", "tf"],
        "PyTorch": ["pytorch"],
        "Docker": ["docker"],
        "Kubernetes": ["kubernetes", "k8s"],
        "AWS": ["aws", "amazon-web-services"],
        "Terraform": ["terraform"],
        "Flutter": ["flutter"],
        "React Native": ["react-native"],
    }
    
    counts: Counter = Counter()
    for r in repos:
        topics = [str(t).lower() for t in r.get("topics", []) if t]
        description = (r.get("description") or "").lower()
        
        for name, keywords in frameworks_tooling.items():
            matched = False
            for kw in keywords:
                if kw in topics or f" {kw} " in f" {description} " or description.startswith(kw) or description.endswith(kw):
                    matched = True
                    break
            if matched:
                counts[name] += 1
                
    return [name for name, _ in counts.most_common(5)]


def audit_habits_and_hygiene(
    repos: list[dict[str, Any]], 
    coder_mood: str,
    total_prs: int = 0,
    total_commits: int = 0
) -> list[str]:
    """Analyze repository structures and metadata to offer actionable recommendations."""
    recommendations: list[str] = []
    
    owned_repos = [r for r in repos if not r.get("fork", False)]
    if owned_repos:
        top_repo = max(owned_repos, key=lambda r: r.get("stargazers_count", 0))
        repo_name = top_repo.get("name", "")
        
        if not top_repo.get("license"):
            recommendations.append(
                f"Add an open-source LICENSE (e.g., MIT) to your top repo '{repo_name}' to encourage community collaboration."
            )
        if not top_repo.get("description"):
            recommendations.append(
                f"Write a short, engaging description for '{repo_name}' to help other developers discover its purpose instantly."
            )
            
    if "Chaotic" in coder_mood:
        recommendations.append(
            "Adopt Conventional Commit prefixes (like 'feat:', 'fix:', 'docs:') to make your repository history look clean and structured."
        )
        
    if total_commits > 50 and total_prs == 0:
        recommendations.append(
            "Try organizing your features into branches and merging them via Pull Requests. It builds standard habits for team settings."
        )
        
    # Default recommendations
    if len(recommendations) < 3:
        recommendations.append(
            "Keep your public repositories organized by adding clean README files with setup instructions."
        )
    if len(recommendations) < 3:
        recommendations.append(
            "Perform code reviews on team members' repositories to level up your collaborative coding habits."
        )
        
    return recommendations[:3]


def calculate_external_contributions(events: list[dict[str, Any]], username: str) -> int:
    """Count the number of public events targeting repositories owned by others."""
    external_count = 0
    for event in events:
        repo_name = event.get("repo", {}).get("name", "")
        if "/" in repo_name:
            owner = repo_name.split("/")[0].lower()
            if owner != username.lower():
                external_count += 1
    return external_count


def generate_markdown_readme(stats: WrappedStats) -> str:
    """Create a copy-pasteable Markdown summary of their Wrapped stats."""
    top_languages_str = ", ".join(lang.name for lang in stats.languages[:3]) or "N/A"
    top_frameworks_str = ", ".join(stats.top_frameworks) or "N/A"
    
    markdown = f"""### 🎁 My GitHub Wrapped {stats.year}

| Metric | Stat |
| :--- | :--- |
| 💻 **Total Commits** | {stats.total_commits:,} |
| ⭐ **Stars Earned** | {stats.total_stars:,} |
| 📦 **Repositories** | {stats.total_repos} |
| 🔥 **Longest Streak** | {stats.longest_streak_days} days |
| 🔤 **Top Languages** | {top_languages_str} |
| 🗂️ **Frameworks Used** | {top_frameworks_str} |
| 🕒 **Chrono-Type** | {stats.chrono_type} |
| 🧘 **Coding Vibe** | {stats.coder_mood} |

> AI personality summary: *"{stats.personality}"*

*Independent recap generated via GitHub Wrapped.*"""
    return markdown.strip()


def build_wrapped_stats(
    username: str,
    profile: dict[str, Any],
    repos: list[dict[str, Any]],
    lang_bytes: dict[str, int],
    contribution_days: list[dict[str, Any]],
    contribution_collection: Optional[dict[str, Any]],
    year: int,
    personality: str = "",
    events: Optional[list[dict[str, Any]]] = None,
) -> WrappedStats:
    """
    Assemble all computed stats into a single WrappedStats response model.
    """
    # ── Top repo ─────────────────────────────────────────────────
    top_name, top_stars, top_lang = find_top_repo(repos)

    # ── Commits, PRs, issues from contribution collection ────────
    total_commits = 0
    total_prs = 0
    total_issues = 0
    if contribution_collection:
        total_commits = contribution_collection.get(
            "totalCommitContributions", 0
        )
        total_prs = contribution_collection.get(
            "totalPullRequestContributions", 0
        )
        total_issues = contribution_collection.get(
            "totalIssueContributions", 0
        )
    else:
        # Approximate from contribution days
        total_commits = sum(d["count"] for d in contribution_days)

    # ── Streaks ──────────────────────────────────────────────────
    longest, current = compute_streaks(contribution_days)

    # ── Activity patterns ────────────────────────────────────────
    busiest_day = compute_busiest_day(contribution_days)
    busiest_month = compute_busiest_month(contribution_days)

    # ── Languages ────────────────────────────────────────────────
    languages = compute_language_breakdown(lang_bytes)

    # ── Stars ────────────────────────────────────────────────────
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)

    # ── Contribution day models ──────────────────────────────────
    contrib_models = [
        ContributionDay(
            date=d["date"],
            count=d["count"],
            level=d.get("level", 0),
        )
        for d in contribution_days
    ]

    # ── Chrono-type, Coder Mood, and Roast parsing ───────────────
    hourly_contribs = [0] * 24
    recent_commits = []
    chrono_type = "Daylight Dev ☀️"
    coder_mood = "Zen Architect 🧘"

    if events:
        hourly_contribs, recent_commits = parse_events_data(events)
        chrono_type = determine_chrono_type(hourly_contribs)
        coder_mood = calculate_coder_mood(recent_commits)

    mood_roast = generate_fallback_roast(coder_mood)

    # ── Phase 2 Developer Utility Calculations ────────────────────
    top_frameworks = analyze_frameworks_and_tools(repos)
    recommendations = audit_habits_and_hygiene(
        repos, coder_mood, total_prs=total_prs, total_commits=total_commits
    )
    
    external_contribs = 0
    if events:
        external_contribs = calculate_external_contributions(events, username)

    stats_obj = WrappedStats(
        username=username,
        avatar_url=profile.get("avatar_url", ""),
        account_created=profile.get("created_at", ""),
        year=year,
        total_commits=total_commits,
        total_stars=total_stars,
        total_repos=len(repos),
        total_prs=total_prs,
        total_issues=total_issues,
        top_repo_name=top_name,
        top_repo_stars=top_stars,
        top_repo_language=top_lang,
        languages=languages,
        longest_streak_days=longest,
        current_streak_days=current,
        busiest_day_of_week=busiest_day,
        busiest_month=busiest_month,
        contributions=contrib_models,
        personality=personality,
        hourly_contributions=hourly_contribs,
        chrono_type=chrono_type,
        coder_mood=coder_mood,
        mood_roast=mood_roast,
        recent_commits=recent_commits,
        recommendations=recommendations,
        external_contributions_count=external_contribs,
        top_frameworks=top_frameworks,
        markdown_readme="",
    )

    stats_obj.markdown_readme = generate_markdown_readme(stats_obj)
    return stats_obj
