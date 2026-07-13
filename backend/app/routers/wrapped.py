"""
API routes for GitHub Wrapped.

Endpoints:
  POST /api/wrapped              — Generate full stats + personality
  GET  /api/wrapped/{username}/image       — Generate and stream PNG card
  GET  /api/wrapped/{username}/personality  — Regenerate personality text
"""

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from backend.app.core.cache import cache_key, get_cache
from backend.app.core.security import limiter
from backend.app.models.schemas import WrappedRequest, WrappedStats
from backend.app.services import ai_service, github_service, image_service
from backend.app.services.stats_engine import build_wrapped_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wrapped", tags=["wrapped"])


@router.post("", response_model=WrappedStats)
@limiter.limit("10/minute")
async def generate_wrapped(request: Request, body: WrappedRequest):
    """
    Main endpoint: fetch GitHub data, compute stats, generate personality.
    Results are cached by (username, year) for the configured TTL.
    """
    cache = get_cache()
    key = cache_key(body.username, body.year)

    # Check cache
    cached = cache.get(key)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1. Fetch user profile
            profile = await github_service.fetch_user_profile(
                client, body.username, body.github_token
            )

            # 2. Fetch all repos
            repos = await github_service.fetch_repos(
                client, body.username, body.github_token
            )

            # 3. Fetch aggregated language bytes
            lang_bytes = await github_service.fetch_all_languages(
                client, body.username, repos, body.github_token
            )

            # 4. Fetch contribution calendar (requires PAT)
            contribution_collection = None
            contribution_days = []
            if body.github_token:
                try:
                    contribution_collection = (
                        await github_service.fetch_contribution_calendar(
                            client, body.username, body.year, body.github_token
                        )
                    )
                    contribution_days = github_service.parse_contribution_days(
                        contribution_collection
                    )
                except Exception as exc:
                    logger.warning(
                        "GraphQL contribution fetch failed: %s", exc
                    )

            # Fallback to public scraping if no token is provided or if GraphQL fails
            if not contribution_days:
                try:
                    contribution_days = await github_service.scrape_public_contribution_calendar(
                        client, body.username, body.year
                    )
                except Exception as exc:
                    logger.warning(
                        "Public contribution calendar scraping failed: %s", exc
                    )

            # 4.5. Fetch public events stream
            events = []
            try:
                events = await github_service.fetch_user_events(
                    client, body.username, body.github_token
                )
            except Exception as exc:
                logger.warning(
                    "Events fetch failed: %s", exc
                )

            # 5. Build stats (without personality first)
            stats = build_wrapped_stats(
                username=body.username,
                profile=profile,
                repos=repos,
                lang_bytes=lang_bytes,
                contribution_days=contribution_days,
                contribution_collection=contribution_collection,
                year=body.year,
                events=events,
            )

            # 6. Generate personality
            stats.personality = await ai_service.generate_personality(stats)

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"GitHub user '{body.username}' not found.",
            )
        if exc.response.status_code == 403:
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit exceeded. Please provide a PAT or try again later.",
            )
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API error: {exc.response.status_code}",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="GitHub API request timed out.",
        )

    # Cache the result
    cache[key] = stats
    return stats


@router.get("/{username}/image")
@limiter.limit("10/minute")
async def generate_image(
    request: Request,
    username: str = Path(
        ...,
        min_length=1,
        max_length=39,
        pattern="^[a-zA-Z0-9-]{1,39}$",
        description="GitHub username to generate image for.",
    ),
    year: int = Query(default=2025, ge=2008, le=2030),
):
    """
    Generate a shareable PNG card. Re-uses cached stats if available,
    otherwise fetches fresh data (without token).
    """
    cache = get_cache()
    key = cache_key(username, year)

    stats: Optional[WrappedStats] = cache.get(key)
    if stats is None:
        # Fetch fresh data via the main endpoint logic (no token is passed)
        body = WrappedRequest(username=username, year=year, github_token=None)
        stats = await generate_wrapped(request, body)

    png_bytes = await run_in_threadpool(image_service.render_card, stats)

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="{username}-wrapped-{year}.png"',
            "Cache-Control": "public, max-age=300",
        },
    )


@router.get("/{username}/personality")
@limiter.limit("15/minute")
async def regenerate_personality(
    request: Request,
    username: str = Path(
        ...,
        min_length=1,
        max_length=39,
        pattern="^[a-zA-Z0-9-]{1,39}$",
        description="GitHub username to regenerate personality for.",
    ),
    year: int = Query(default=2025, ge=2008, le=2030),
):
    """
    Re-roll the personality text for an already-cached user.
    Returns 404 if the user hasn't been wrapped yet.
    """
    cache = get_cache()
    key = cache_key(username, year)

    stats: Optional[WrappedStats] = cache.get(key)
    if stats is None:
        raise HTTPException(
            status_code=404,
            detail="No cached Wrapped data found. Generate a Wrapped first.",
        )

    stats.personality = await ai_service.generate_personality(stats)
    cache[key] = stats

    return {"personality": stats.personality}
