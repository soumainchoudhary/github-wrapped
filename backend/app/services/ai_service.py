"""
AI personality generator — queries HuggingFace Serverless Inference API
for a fun two-sentence coding personality summary.

Falls back to a deterministic rule-based generator when:
  1. No HF_API_TOKEN is configured.
  2. The API returns an error / rate-limit.
  3. The request times out (configurable, default 3 s).
"""

from __future__ import annotations

import logging
import random
from typing import Any, Optional

import httpx

from backend.app.core.config import settings
from backend.app.models.schemas import WrappedStats

logger = logging.getLogger(__name__)

HF_API_URL = "https://api-inference.huggingface.co/models/{model_id}"


# ── HuggingFace API call ────────────────────────────────────────────────────

async def generate_personality_hf(stats: WrappedStats) -> Optional[str]:
    """
    Ask the HuggingFace Inference API for a personality blurb.
    Returns None on any failure so the caller can fall back.
    """
    if not settings.hf_api_token:
        return None

    top_langs = ", ".join(l.name for l in stats.languages[:3]) or "unknown"
    prompt = (
        f"You are a witty coding personality analyst. "
        f"Given these GitHub stats for {stats.username}: "
        f"{stats.total_commits} commits, "
        f"top languages: {top_langs}, "
        f"longest streak: {stats.longest_streak_days} days, "
        f"{stats.total_stars} stars earned, "
        f"busiest day: {stats.busiest_day_of_week}. "
        f"Write exactly two fun, encouraging sentences describing their "
        f"coding personality. Be creative and use emojis."
    )

    url = HF_API_URL.format(model_id=settings.hf_model_id)

    try:
        async with httpx.AsyncClient(
            timeout=settings.hf_timeout_seconds
        ) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.hf_api_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 100,
                        "temperature": 0.8,
                        "return_full_text": False,
                    },
                },
            )

            if resp.status_code != 200:
                logger.warning(
                    "HF API returned %d: %s", resp.status_code, resp.text
                )
                return None

            data = resp.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "").strip()
            return None

    except (httpx.TimeoutException, httpx.HTTPError) as exc:
        logger.warning("HF API request failed: %s", exc)
        return None


# ── Rule-based fallback ─────────────────────────────────────────────────────

# Personality archetypes keyed by traits
_ARCHETYPES: list[dict[str, Any]] = [
    {
        "name": "The Marathon Coder",
        "condition": lambda s: s.longest_streak_days >= 30,
        "templates": [
            "🏃 You're a coding marathon champion with a {streak}-day streak! Your keyboard probably files for overtime pay.",
            "🔥 {streak} days of non-stop commits? Your consistency is the stuff of legends! Bugs don't stand a chance against your relentless energy.",
        ],
    },
    {
        "name": "The Polyglot",
        "condition": lambda s: len(s.languages) >= 4,
        "templates": [
            "🌐 A true polyglot coder — you've mastered {lang_count} languages like a programming United Nations! Your versatility is your superpower.",
            "🗣️ {lang_count} languages in your arsenal? You collect programming languages like some people collect stamps — but way cooler.",
        ],
    },
    {
        "name": "The Star Collector",
        "condition": lambda s: s.total_stars >= 50,
        "templates": [
            "⭐ With {stars} stars shining bright, you're basically the North Star of open source! Developers look to your repos for guidance.",
            "🌟 {stars} GitHub stars! Your code doesn't just work — it inspires. Keep lighting up the open-source sky!",
        ],
    },
    {
        "name": "The Weekend Warrior",
        "condition": lambda s: s.busiest_day_of_week in ("Saturday", "Sunday"),
        "templates": [
            "🎮 While others rest, you code! Your busiest day is {day} — proof that passion knows no weekends.",
            "☕ A {day} coder? Your side projects have side projects! That weekend dedication is seriously impressive.",
        ],
    },
    {
        "name": "The Consistent Contributor",
        "condition": lambda s: s.total_commits >= 200,
        "templates": [
            "📊 {commits} commits this year — you treat coding like a daily habit, not a hobby! Consistency is your middle name.",
            "💪 With {commits} commits under your belt, you've proven that showing up every day is the ultimate superpower.",
        ],
    },
]

_FALLBACK_TEMPLATES = [
    "🚀 You've been on a coding adventure this year with {commits} commits across {repos} repos! Your {top_lang} skills are definitely leveling up.",
    "💻 {commits} commits, {repos} repos, and a passion for {top_lang} — you're writing your own success story, one commit at a time!",
    "🎯 From {top_lang} to everything in between, your {commits} commits show a developer who's always learning. The best is yet to come!",
]


def generate_personality_fallback(stats: WrappedStats) -> str:
    """
    Deterministic (but fun) rule-based personality generator.
    Picks the first matching archetype or uses a generic fallback.
    """
    top_lang = stats.languages[0].name if stats.languages else "code"

    # Try archetypes in order
    for archetype in _ARCHETYPES:
        if archetype["condition"](stats):
            template = random.choice(archetype["templates"])
            return template.format(
                streak=stats.longest_streak_days,
                lang_count=len(stats.languages),
                stars=stats.total_stars,
                day=stats.busiest_day_of_week,
                commits=stats.total_commits,
                repos=stats.total_repos,
                top_lang=top_lang,
            )

    # Generic fallback
    template = random.choice(_FALLBACK_TEMPLATES)
    return template.format(
        commits=stats.total_commits,
        repos=stats.total_repos,
        top_lang=top_lang,
    )


async def generate_roast_hf(stats: WrappedStats) -> Optional[str]:
    """
    Ask the Hugging Face Inference API for a roast based on recent commits.
    """
    if not settings.hf_api_token:
        return None
    if not stats.recent_commits:
        return None

    # Take a small sample of unique commit messages to stay within token limits
    commits_sample = "; ".join(stats.recent_commits[:6])
    prompt = (
        f"You are a sarcastic, witty developer roast bot. "
        f"Analyze these recent commit messages from {stats.username}: "
        f"[{commits_sample}]. "
        f"Write a hilarious, sarcastic one-sentence roast of their commit messages. "
        f"Make it funny and sharp but keep it clean. Do not exceed one sentence."
    )

    url = HF_API_URL.format(model_id=settings.hf_model_id)

    try:
        async with httpx.AsyncClient(
            timeout=settings.hf_timeout_seconds
        ) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.hf_api_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 80,
                        "temperature": 0.85,
                        "return_full_text": False,
                    },
                },
            )

            if resp.status_code != 200:
                return None

            data = resp.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "").strip()
            return None

    except Exception:
        return None


async def generate_personality(stats: WrappedStats) -> str:
    """
    Main entry point. Tries HF first for personality and roast,
    falling back gracefully on either failure.
    """
    # 1. Generate personality summary
    personality = await generate_personality_hf(stats)
    if not personality:
        personality = generate_personality_fallback(stats)
    
    # 2. Generate AI commit roast
    ai_roast = await generate_roast_hf(stats)
    if ai_roast:
        stats.mood_roast = ai_roast
        
    return personality
