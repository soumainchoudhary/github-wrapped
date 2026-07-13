"""
GitHub API client — fetches user profile, repos, and contribution calendar.

Uses:
  • REST API v3 for user profile and repositories.
  • GraphQL API v4 for the contribution calendar (requires a PAT).
  
Falls back gracefully when no PAT is provided (GraphQL is skipped).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any, Optional

import httpx
import re

logger = logging.getLogger(__name__)

GITHUB_REST = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"

# Standard language → color mapping (top languages only; GitHub API provides this too)
LANG_COLORS: dict[str, str] = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "C#": "#178600",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
    "Dart": "#00B4AB",
    "Lua": "#000080",
    "Scala": "#c22d40",
    "R": "#198CE7",
    "Jupyter Notebook": "#DA5B0B",
    "Vue": "#41b883",
}


def _headers(token: Optional[str] = None) -> dict[str, str]:
    """Build request headers, optionally adding an auth token."""
    h: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


async def fetch_user_profile(
    client: httpx.AsyncClient,
    username: str,
    token: Optional[str] = None,
) -> dict[str, Any]:
    """GET /users/{username}"""
    resp = await client.get(
        f"{GITHUB_REST}/users/{username}",
        headers=_headers(token),
    )
    resp.raise_for_status()
    return resp.json()


async def fetch_repos(
    client: httpx.AsyncClient,
    username: str,
    token: Optional[str] = None,
    *,
    max_pages: int = 10,
) -> list[dict[str, Any]]:
    """
    Paginate through GET /users/{username}/repos to get all public repos.
    """
    repos: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        resp = await client.get(
            f"{GITHUB_REST}/users/{username}/repos",
            headers=_headers(token),
            params={
                "type": "owner",
                "sort": "updated",
                "per_page": 100,
                "page": page,
            },
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
    return repos


async def fetch_user_events(
    client: httpx.AsyncClient,
    username: str,
    token: Optional[str] = None,
    *,
    max_pages: int = 3,
) -> list[dict[str, Any]]:
    """
    Fetch the user's public activity stream from GET /users/{username}/events.
    Paginate up to max_pages (default 3) to retrieve recent commit patterns.
    """
    events: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        resp = await client.get(
            f"{GITHUB_REST}/users/{username}/events",
            headers=_headers(token),
            params={
                "per_page": 100,
                "page": page,
            },
        )
        if resp.status_code != 200:
            break
        batch = resp.json()
        if not batch:
            break
        events.extend(batch)
    return events


def extract_languages_from_repos(
    repos: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Extract language data from the repos list we already fetched.
    Uses the `language` and `size` fields already present in each repo object,
    avoiding separate API calls per repo and eliminating rate-limit issues.
    """
    totals: dict[str, int] = {}
    for r in repos:
        if r.get("fork", False):
            continue
        lang = r.get("language")
        if lang:
            # Use repo size in KB as a proxy for language bytes
            size = r.get("size", 0) * 1024  # GitHub reports size in KB
            totals[lang] = totals.get(lang, 0) + size
    return totals


# ── GraphQL: Contribution Calendar ──────────────────────────────────────────

CONTRIBUTION_QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""

LEVEL_MAP = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


async def fetch_contribution_calendar(
    client: httpx.AsyncClient,
    username: str,
    year: int,
    token: str,
) -> dict[str, Any]:
    """
    Query the GitHub GraphQL API for the user's contribution calendar.
    Requires a PAT (GraphQL is authenticated-only).
    Returns the raw contributionsCollection dict.
    """
    from_dt = f"{year}-01-01T00:00:00Z"
    to_dt = f"{year}-12-31T23:59:59Z"

    resp = await client.post(
        GITHUB_GRAPHQL,
        headers=_headers(token),
        json={
            "query": CONTRIBUTION_QUERY,
            "variables": {
                "username": username,
                "from": from_dt,
                "to": to_dt,
            },
        },
    )
    resp.raise_for_status()
    data = resp.json()

    if "errors" in data:
        logger.error("GraphQL errors: %s", data["errors"])
        raise httpx.HTTPStatusError(
            message=str(data["errors"]),
            request=resp.request,
            response=resp,
        )

    return data["data"]["user"]["contributionsCollection"]


def parse_contribution_days(
    collection: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Flatten the nested weeks → contributionDays structure into a flat list
    of {date, count, level} dicts.
    """
    days: list[dict[str, Any]] = []
    calendar = collection.get("contributionCalendar", {})
    for week in calendar.get("weeks", []):
        for day in week.get("contributionDays", []):
            days.append(
                {
                    "date": date.fromisoformat(day["date"]),
                    "count": day["contributionCount"],
                    "level": LEVEL_MAP.get(day.get("contributionLevel", "NONE"), 0),
                }
            )
    return days


async def scrape_public_contribution_calendar(
    client: httpx.AsyncClient,
    username: str,
    year: int,
) -> list[dict[str, Any]]:
    """
    Scrape the public GitHub contribution calendar page when no PAT is provided.
    Returns a flat list of dicts: [{"date": date, "count": int, "level": int}].
    """
    url = f"https://github.com/users/{username}/contributions?from={year}-01-01&to={year}-12-31"
    resp = await client.get(url)
    if resp.status_code != 200:
        logger.warning("Failed to fetch public contributions page: HTTP %d", resp.status_code)
        return []
    
    html = resp.text
    
    # Parse td elements: <td ... data-date="YYYY-MM-DD" ... id="ID" ... data-level="LEVEL" ... class="ContributionCalendar-day">
    td_pattern = re.compile(
        r'<td[^>]*data-date="([^"]+)"[^>]*id="([^"]+)"[^>]*data-level="([^"]+)"[^>]*class="[^"]*ContributionCalendar-day[^"]*"[^>]*>'
    )
    tds = td_pattern.findall(html)
    
    # Parse tooltips by "for" attribute
    tooltip_pattern = re.compile(r'<tool-tip[^>]*for="([^"]+)"[^>]*>(.*?)</tool-tip>', re.DOTALL)
    tooltips = {for_id: text.strip() for for_id, text in tooltip_pattern.findall(html)}
    
    days = []
    for date_str, element_id, level in tds:
        tooltip_text = tooltips.get(element_id, "")
        count = 0
        if tooltip_text:
            if tooltip_text.startswith("No contributions"):
                count = 0
            else:
                match = re.match(r"(\d+)\s+contribution", tooltip_text)
                if match:
                    count = int(match.group(1))
                else:
                    try:
                        count = int(level)
                    except ValueError:
                        count = 0
        else:
            try:
                count = int(level)
            except ValueError:
                count = 0
                
        try:
            d = date.fromisoformat(date_str)
            days.append({
                "date": d,
                "count": count,
                "level": int(level)
            })
        except ValueError:
            pass
            
    return days
