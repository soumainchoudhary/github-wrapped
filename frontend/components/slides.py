"""
Slide renderers for the Streamlit Wrapped experience.

Each function renders one "slide" in the step-by-step reveal flow.
"""

from __future__ import annotations

from typing import Any
import html

import streamlit as st

from components.charts import (
    contribution_heatmap,
    language_donut,
    streak_chart,
    hourly_radar_chart,
)


def render_html_clean(html_str: str):
    """
    Renders HTML in Streamlit safely by using st.html.
    """
    st.html(html_str)


def render_landing():
    """Slide 0 — Landing / input page."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 3.5rem; font-weight: 800; color: #ffffff;
                        letter-spacing: -1.5px; margin-bottom: 0.5rem; line-height: 1.1;">
                GitHub Wrapped
            </h1>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.15rem; max-width: 600px; margin: 0.5rem auto 1.5rem auto; font-weight: 400; line-height: 1.6;">
                Discover your year in code — commits, streaks, languages, and your
                AI-generated coding personality.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input(
            "GitHub Username",
            placeholder="e.g. torvalds",
            key="input_username",
            help="Your public GitHub username.",
        )
        year = st.selectbox(
            "Year",
            options=list(range(2025, 2007, -1)),
            index=0,
            key="input_year",
        )

        generate = st.button(
            "Unwrap My Year",
            use_container_width=True,
            type="primary",
        )

    st.markdown(
        """
        <div style="text-align: center; margin-top: 2rem; opacity: 0.3; font-size: 0.75rem; color: #ffffff; line-height: 1.4;">
            This project is an independent open-source tool and is not affiliated with, authorized,<br/>
            maintained, or endorsed by GitHub, Inc. or Microsoft.
        </div>
        """,
        unsafe_allow_html=True,
    )

    return username, year, generate


def render_commits_headline(stats: dict[str, Any]):
    """Slide 1 — Big commit number."""
    st.markdown(
        f"""
        <div class="glass-card" style="text-align: center; margin-bottom: 2rem; border-color: rgba(255,255,255,0.06) !important;">
            <p style="color: rgba(255,255,255,0.4); font-size: 1.05rem; text-transform: uppercase;
                      letter-spacing: 0.15em; margin-bottom: 0.5rem; font-weight: 600;">
                Your {stats['year']} in code
            </p>
            <h1 style="font-size: 6.5rem; font-weight: 800; background: linear-gradient(135deg, #ffffff, #a8acb3);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0.25rem 0;
                        letter-spacing: -2.5px; line-height: 1;">
                {stats['total_commits']:,}
            </h1>
            <p style="color: #ffffff; font-size: 1.5rem; font-weight: 500; margin-top: 0.5rem; opacity: 0.95;">
                commits pushed
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Stars Earned", f"{stats['total_stars']:,}")
    c2.metric("Repositories", stats["total_repos"])
    c3.metric("Pull Requests", stats.get("total_prs", 0))


def render_languages(stats: dict[str, Any]):
    """Slide 2 — Top languages donut chart."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 700; font-size: 2rem; letter-spacing: -0.5px;">Your Top Languages</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">The tongues you spoke to machines this year</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    languages = stats.get("languages", [])
    if languages:
        fig = language_donut(languages)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Single HTML block for language details and progress bars
        lang_html = '<div class="glass-card" style="padding: 1.5rem 2rem !important; margin-top: 1rem; border-color: rgba(255,255,255,0.06) !important;">'
        for lang in languages[:5]:
            color = lang.get("color", "#8b949e")
            pct = lang["percentage"]
            lang_name = html.escape(str(lang.get('name', 'Unknown')))
            lang_html += f"""
            <div style="margin-bottom: 1.25rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-weight: 500; font-size: 1rem; color: #ffffff;">
                    <span><span style="color: {color}; margin-right: 0.6rem; font-size: 1.1rem;">●</span>{lang_name}</span>
                    <span style="opacity: 0.85;">{pct}%</span>
                </div>
                <div style="background: rgba(255,255,255,0.05); height: 8px; border-radius: 4px; overflow: hidden; border: 1px solid rgba(255,255,255,0.02);">
                    <div style="background: {color}; width: {pct}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
            """
        lang_html += '</div>'
        render_html_clean(lang_html)
    else:
        st.info("No language data available.")


def render_streaks(stats: dict[str, Any]):
    """Slide 3 — Streak breakdown."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 700; font-size: 2rem; letter-spacing: -0.5px;">Your Coding Streaks</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">Consistency is the name of the game</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    fig = streak_chart(
        stats.get("longest_streak_days", 0),
        stats.get("current_streak_days", 0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    col1, col2 = st.columns(2)
    col1.metric("Busiest Day", stats.get("busiest_day_of_week", "N/A"))
    col2.metric("Busiest Month", stats.get("busiest_month", "N/A"))


def render_heatmap(stats: dict[str, Any]):
    """Slide 4 — Contribution calendar heatmap."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 700; font-size: 2rem; letter-spacing: -0.5px;">Contribution Calendar</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">Every green square tells a story</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    contributions = stats.get("contributions", [])
    if contributions:
        fig = contribution_heatmap(contributions, stats.get("year", 2025))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info(
            "📌 Contribution calendar requires a GitHub PAT. "
            "Add one to see your heatmap!"
        )


def render_personality(stats: dict[str, Any]):
    """Slide 5 — AI personality card."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 700; font-size: 2rem; letter-spacing: -0.5px;">Your Coding Personality</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">AI-powered analysis of your coding style</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    personality = html.escape(str(stats.get("personality", "")))
    if personality:
        st.markdown(
            f"""
            <div class="glass-card" style="border-color: rgba(255, 255, 255, 0.08) !important;
                                          text-align: center; padding: 2.25rem !important;">
                <p style="color: #ffffff; font-size: 1.3rem; line-height: 1.7; font-weight: 400; opacity: 0.9;">
                    "{personality}"
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("Personality text could not be generated.")

    if stats.get("top_repo_name"):
        top_repo = html.escape(str(stats.get('top_repo_name', '')))
        top_lang = html.escape(str(stats.get('top_repo_language', 'N/A')))
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center; padding: 1.5rem !important; max-width: 480px; margin: 1.25rem auto !important; border-color: rgba(255,255,255,0.06) !important;">
                <p style="color: rgba(255, 255, 255, 0.4); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.4rem; font-weight: 600;">🏆 Your crown jewel</p>
                <h3 style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin: 0.25rem 0;">{top_repo}</h3>
                <p style="color: rgba(255, 255, 255, 0.6); font-size: 1.05rem; margin-top: 0.4rem; font-weight: 500;">
                    ⭐ {stats.get('top_repo_stars', 0):,} stars  •  
                    <span>{top_lang}</span>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_share(stats: dict[str, Any], api_base: str):
    """Slide 6 — Download / share card."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 700; font-size: 2rem; letter-spacing: -0.5px;">Share Your Wrapped</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">Download your card and show the world!</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    username = html.escape(str(stats.get("username", "")))
    year = stats.get("year", 2025)
    image_url = f"{api_base}/api/wrapped/{username}/image?year={year}"
    markdown_card = html.escape(str(stats.get("markdown_readme", "")))
    share_html = f"""
    <div class="glass-card" style="text-align: center; max-width: 550px; margin: 1.5rem auto !important; padding: 2rem !important; border-color: rgba(255,255,255,0.06) !important;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem; opacity: 0.95;">🎴</div>
        <h3 style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">Your Wrapped Card is Ready!</h3>
        <p style="color: rgba(255, 255, 255, 0.45); font-size: 0.95rem; max-width: 360px; margin: 0 auto 1.5rem auto; line-height: 1.5;">
            Download your custom-designed recap image to share on social media.
        </p>
        <a href="{image_url}" target="_blank" download="github-wrapped-{username}.png"
           style="display: inline-block; padding: 0.8rem 2.25rem;
                  background: rgba(255, 255, 255, 0.95);
                  color: #0b0d13 !important; text-decoration: none; border-radius: 10px;
                  font-weight: 600; font-size: 1.1rem;
                  transition: transform 0.2s ease, background 0.2s ease;">
            Download PNG Card
        </a>
    </div>

    <div class="glass-card" style="max-width: 550px; margin: 1.5rem auto !important; padding: 2rem !important; border-color: rgba(255,255,255,0.06) !important;">
        <h3 style="color: #ffffff; font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem; text-align: center;">📄 GitHub Profile README Card</h3>
        <p style="color: rgba(255, 255, 255, 0.45); font-size: 0.92rem; line-height: 1.4; text-align: center; margin-bottom: 1.5rem;">
            Copy this Markdown snippet to showcase your {year} developer stats directly on your GitHub profile.
        </p>
        <!-- Styled Terminal Code block with glassmorphism -->
        <div style="background: rgba(18, 18, 18, 0.55); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; overflow: hidden; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);">
            <!-- Terminal Header -->
            <div style="background: rgba(255, 255, 255, 0.03); padding: 0.6rem 1rem; display: flex; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
                <div style="display: flex; gap: 6px; margin-right: auto;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #ff5f56; display: inline-block;"></span>
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #ffbd2e; display: inline-block;"></span>
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #27c93f; display: inline-block;"></span>
                </div>
                <div style="color: rgba(255, 255, 255, 0.35); font-size: 0.75rem; font-family: monospace; letter-spacing: 0.5px;">wrapped-profile.md</div>
            </div>
            <!-- Code Area -->
            <pre style="font-family: monospace; font-size: 0.82rem; overflow-x: auto; white-space: pre-wrap; padding: 1.25rem; color: rgba(255, 255, 255, 0.9); max-height: 250px; text-align: left; margin: 0; background: transparent; border: none;">{markdown_card}</pre>
        </div>
    </div>

    <p style='text-align: center; color: rgba(255, 255, 255, 0.35); margin-top: 2rem; font-size: 0.9rem;'>
        Built with ❤️ using FastAPI, Streamlit & AI
    </p>
    """
    render_html_clean(share_html)


# ── Enhancements: Chrono-Type, Coder Mood, and Battle Mode Slides ───────────

def render_chrono_type(stats: dict[str, Any]):
    """Slide 3 — Developer Chrono-Type and Clock."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 700; font-size: 2rem; letter-spacing: -0.5px;">Your Coding Chrono-Type</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">When are you most productive during the day?</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    chrono_name = html.escape(str(stats.get("chrono_type", "Daylight Dev ☀️")))
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown(
            f"""
            <div class="glass-card" style="border-color: rgba(255, 255, 255, 0.08) !important; padding: 1.75rem !important; margin-top: 1.5rem;">
                <p style="color: rgba(255, 255, 255, 0.4); font-size: 0.95rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.1em;">Daily Rhythm</p>
                <h3 style="color: #ffffff; font-size: 1.8rem; font-weight: 800; margin: 0.5rem 0; line-height: 1.2;">{chrono_name}</h3>
                <p style="color: rgba(255, 255, 255, 0.7); font-size: 1rem; line-height: 1.6; margin-top: 0.75rem;">
                    Your commits are compiled into 24 hourly bins (UTC). This represents your natural coding clock!
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    with col2:
        hourly_data = stats.get("hourly_contributions", [0]*24)
        fig = hourly_radar_chart(hourly_data)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_coder_mood(stats: dict[str, Any]):
    """Slide 6 — Coder Mood & Commit Roast."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 700; font-size: 2rem; letter-spacing: -0.5px;">Coder Mood & Roast</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">How your commits sound to the world</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mood = html.escape(str(stats.get("coder_mood", "Zen Architect 🧘")))
    roast = html.escape(str(stats.get("mood_roast", "No roast available.")))

    st.markdown(
        f"""
        <div class="glass-card" style="border-color: rgba(255, 255, 255, 0.08) !important; text-align: center; padding: 2rem !important; margin-bottom: 1.5rem;">
            <p style="color: rgba(255, 255, 255, 0.4); font-size: 0.95rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Vibe Assessment</p>
            <h2 style="color: #ffffff; font-size: 2.2rem; font-weight: 800; margin: 0.5rem 0;">{mood}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="glass-card" style="border-color: rgba(239, 68, 68, 0.25) !important; background: rgba(239, 68, 68, 0.03) !important; padding: 2rem !important;">
            <p style="color: #ef4444; font-size: 0.95rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.15em; margin-bottom: 0.5rem;">🔥 AI Commit Roast</p>
            <p style="color: #ffffff; font-size: 1.25rem; font-weight: 400; line-height: 1.6; opacity: 0.9; margin: 0;">
                "{roast}"
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_battle_faceoff(p1: dict[str, Any], p2: dict[str, Any]):
    """Versus Slide 1 — Faceoff card."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 800; font-size: 2.2rem; letter-spacing: -1px;">THE FACE-OFF</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">Matchup Overview</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col_vs, col2 = st.columns([1, 0.3, 1])

    p1_user = html.escape(str(p1.get('username', '')))
    p2_user = html.escape(str(p2.get('username', '')))
    p1_avatar = html.escape(str(p1.get('avatar_url', '')))
    p2_avatar = html.escape(str(p2.get('avatar_url', '')))

    with col1:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center; padding: 2rem 1.5rem !important; border-color: rgba(56, 189, 248, 0.3) !important;">
                <img src="{p1_avatar}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #38bdf8; margin-bottom: 1rem;"/>
                <h3 style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin: 0.25rem 0;">@{p1_user}</h3>
                <p style="color: rgba(255, 255, 255, 0.4); font-size: 0.9rem; margin-top: 0.25rem;">Joined {p1.get('account_created', 'N/A')[:10] if p1.get('account_created') else 'N/A'}</p>
                <hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.08); margin: 1rem 0;"/>
                <p style="color: #ffffff; font-size: 1.05rem; font-weight: 500;">📦 {p1['total_repos']} Repositories</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_vs:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 4.5rem;">
                <h1 style="color: #ef4444; font-size: 2.5rem; font-weight: 900; font-style: italic; letter-spacing: -2px;">VS</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center; padding: 2rem 1.5rem !important; border-color: rgba(139, 92, 246, 0.3) !important;">
                <img src="{p2_avatar}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #8b5cf6; margin-bottom: 1rem;"/>
                <h3 style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin: 0.25rem 0;">@{p2_user}</h3>
                <p style="color: rgba(255, 255, 255, 0.4); font-size: 0.9rem; margin-top: 0.25rem;">Joined {p2.get('account_created', 'N/A')[:10] if p2.get('account_created') else 'N/A'}</p>
                <hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.08); margin: 1rem 0;"/>
                <p style="color: #ffffff; font-size: 1.05rem; font-weight: 500;">📦 {p2['total_repos']} Repositories</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_battle_stats_duel(p1: dict[str, Any], p2: dict[str, Any]):
    """Versus Slide 2 — Stats comparison table/list."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 800; font-size: 2.2rem; letter-spacing: -1px;">STATS DUEL</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">Head-to-Head Comparison</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metrics = [
        ("total_commits", "Total Commits 💻"),
        ("total_stars", "Stars Earned ⭐"),
        ("longest_streak_days", "Longest Streak 🔥"),
        ("total_prs", "Pull Requests 📦"),
    ]

    for key, label in metrics:
        v1 = p1.get(key, 0)
        v2 = p2.get(key, 0)
        
        p1_win = v1 > v2
        p2_win = v2 > v1
        
        p1_color = "#38bdf8" if p1_win else ("#e6edf3" if v1 == v2 else "rgba(255,255,255,0.25)")
        p2_color = "#8b5cf6" if p2_win else ("#e6edf3" if v1 == v2 else "rgba(255,255,255,0.25)")
        
        p1_badge = "👑" if p1_win else "&nbsp;&nbsp;"
        p2_badge = "👑" if p2_win else "&nbsp;&nbsp;"

        render_html_clean(
            f"""
            <div class="glass-card" style="padding: 1rem 1.5rem !important; margin-bottom: 0.75rem; border-color: rgba(255,255,255,0.04) !important;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 1.25rem; font-weight: 700; color: {p1_color}; width: 30%; text-align: left;">
                        {p1_badge} {v1:,}
                    </div>
                    <div style="font-size: 0.95rem; font-weight: 600; color: rgba(255, 255, 255, 0.5); text-align: center; width: 40%; text-transform: uppercase; letter-spacing: 0.05em;">
                        {label}
                      </div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: {p2_color}; width: 30%; text-align: right;">
                        {v2:,} {p2_badge}
                    </div>
                </div>
            </div>
            """
        )


def render_battle_verdict(p1: dict[str, Any], p2: dict[str, Any]):
    """Versus Slide 3 — The Verdict and compatibility scoring."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 800; font-size: 2.2rem; letter-spacing: -1px;">BATTLE VERDICT</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">The Final Decision</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    p1_score = 0
    p2_score = 0
    
    metrics = ["total_commits", "total_stars", "longest_streak_days", "total_prs"]
    for key in metrics:
        v1 = p1.get(key, 0)
        v2 = p2.get(key, 0)
        if v1 > v2:
            p1_score += 1
        elif v2 > v1:
            p2_score += 1

    if p1_score > p2_score:
        winner_name = html.escape(f"@{p1.get('username', '')}")
        winner_color = "#38bdf8"
        verdict_text = f"Winner by stats: {winner_name}! Their sheer keyboard muscle overcame the opponent."
        win_avatar = html.escape(str(p1.get("avatar_url", "")))
    elif p2_score > p1_score:
        winner_name = html.escape(f"@{p2.get('username', '')}")
        winner_color = "#8b5cf6"
        verdict_text = f"Winner by stats: {winner_name}! A dominating performance across the metrics."
        win_avatar = html.escape(str(p2.get("avatar_url", "")))
    else:
        winner_name = "Draw!"
        winner_color = "#ffffff"
        verdict_text = "It's a dead tie! Both developers possess equal, legendary engineering powers."
        win_avatar = ""

    p1_langs = [html.escape(str(l.get("name", ""))) for l in p1.get("languages", [])[:2]]
    p2_langs = [html.escape(str(l.get("name", ""))) for l in p2.get("languages", [])[:2]]
    
    shared = set(p1_langs).intersection(set(p2_langs))
    if len(shared) >= 2:
        synergy = "95% (Perfect Synergy) 🤝"
        synergy_desc = "You speak the exact same programming dialects! A perfect pairing for a code sprint."
    elif len(shared) == 1:
        synergy = "65% (Cooperative Vibe) 👥"
        synergy_desc = "You share common ground! A solid team dynamic that can bridge stack gaps."
    else:
        synergy = "30% (Tech Clash) ⚡"
        synergy_desc = "Opposite poles! You use completely distinct tech stacks. Dynamic but chaotic."

    col1, col2 = st.columns([1, 1.1])
    p1_user = html.escape(str(p1.get('username', '')))
    p2_user = html.escape(str(p2.get('username', '')))
    
    with col1:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center; padding: 1.75rem !important; border-color: {winner_color} !important; height: 320px;">
                <p style="color: {winner_color}; font-size: 0.95rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.15em; margin-bottom: 0.5rem;">👑 Champion</p>
                {f'<img src="{win_avatar}" style="width: 70px; height: 70px; border-radius: 50%; border: 3px solid {winner_color}; margin-bottom: 0.5rem;"/>' if win_avatar else '<div style="font-size: 3.5rem; margin-bottom: 0.5rem;">🤝</div>'}
                <h3 style="color: #ffffff; font-size: 1.5rem; font-weight: 800; margin: 0.25rem 0;">{winner_name}</h3>
                <p style="color: rgba(255, 255, 255, 0.7); font-size: 0.92rem; line-height: 1.5; margin-top: 0.5rem;">
                    {verdict_text}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="glass-card" style="border-color: rgba(255, 255, 255, 0.08) !important; padding: 1.75rem !important; height: 320px;">
                <p style="color: rgba(255, 255, 255, 0.4); font-size: 0.95rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Language Synergy</p>
                <h3 style="color: #ffffff; font-size: 1.25rem; font-weight: 800; margin: 0.25rem 0;">{synergy}</h3>
                <p style="color: rgba(255, 255, 255, 0.65); font-size: 0.92rem; line-height: 1.5; margin-top: 0.5rem;">
                    {synergy_desc}
                </p>
                <hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.08); margin: 0.5rem 0;"/>
                <p style="color: rgba(255, 255, 255, 0.4); font-size: 0.8rem; margin-top: 0.25rem; line-height: 1.3;">
                    Top languages:<br/>
                    <b>@{p1_user}:</b> {", ".join(p1_langs)}<br/>
                    <b>@{p2_user}:</b> {", ".join(p2_langs)}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Phase 2 Developer Utility Slides ──────────────────────────────────────────

def render_frameworks_stack(stats: dict[str, Any]):
    """Slide 2.5 — Frameworks & Tools Stack."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 700; font-size: 2rem; letter-spacing: -0.5px;">Frameworks & Tools Stack</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">The libraries, engines, and environments that powered your build</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    frameworks = stats.get("top_frameworks", [])
    if frameworks:
        tags_html = """
        <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 1rem; margin-top: 1.5rem; margin-bottom: 2rem;">
        """
        color_palette = [
            ("linear-gradient(135deg, #61dafb, #2188ff)", "#051e3e"), # react blue
            ("linear-gradient(135deg, #009485, #005953)", "#ffffff"), # fastapi green/teal
            ("linear-gradient(135deg, #38bdf8, #0ea5e9)", "#0f172a"), # docker light blue
            ("linear-gradient(135deg, #ee4c2c, #b32a0f)", "#ffffff"), # pytorch red
            ("linear-gradient(135deg, #326ce5, #1d4ed8)", "#ffffff"), # kubernetes dark blue
            ("linear-gradient(135deg, #a78bfa, #7c3aed)", "#ffffff"), # default purple
        ]
        
        for idx, fw in enumerate(frameworks):
            grad, text_color = color_palette[idx % len(color_palette)]
            fw_clean = html.escape(str(fw))
            tags_html += f"""
            <div style="background: {grad}; color: {text_color}; padding: 0.75rem 1.5rem; border-radius: 50px; font-weight: 700; font-size: 1.15rem; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.1); display: flex; align-items: center; justify-content: center; min-width: 120px;">
                {fw_clean}
            </div>
            """
        tags_html += "</div>"
        render_html_clean(tags_html)
        
        st.markdown(
            f"""
            <div class="glass-card" style="border-color: rgba(255,255,255,0.06) !important; padding: 1.75rem !important; text-align: center; max-width: 550px; margin: 0 auto;">
                <p style="color: rgba(255, 255, 255, 0.4); font-size: 0.95rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Stack Summary</p>
                <p style="color: #ffffff; font-size: 1.15rem; line-height: 1.6; opacity: 0.9; margin: 0;">
                    You integrated <b>{len(frameworks)}</b> major framework{"s" if len(frameworks) > 1 else ""} across your repositories, showcasing strong capabilities in {" & ".join([html.escape(str(f)) for f in frameworks[:2]])}.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="glass-card" style="border-color: rgba(255,255,255,0.06) !important; padding: 2rem !important; text-align: center; max-width: 500px; margin: 2rem auto;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📦</div>
                <p style="color: #ffffff; font-size: 1.1rem; opacity: 0.8; margin-bottom: 0;">
                    No frameworks or DevOps tools detected in your repository topics or descriptions.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_open_source_impact(stats: dict[str, Any]):
    """Slide 4.5 — Open-Source Impact Tracker."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 700; font-size: 2rem; letter-spacing: -0.5px;">Open-Source Impact</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">Your contributions to the wider developer ecosystem</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    external_count = stats.get("external_contributions_count", 0)
    
    if external_count > 20:
        badge = "🌍 OSS Champion"
        desc = "You are a driving force in open-source! Collaborating across borders and building libraries for everyone."
        color = "#10b981"
    elif external_count > 5:
        badge = "🤝 Collaborative Coder"
        desc = "You actively venture out of your own backyard to help other projects grow. Keep building!"
        color = "#3b82f6"
    elif external_count > 0:
        badge = "🌱 Rising Contributor"
        desc = "You've dipped your toes into external repos. Every contribution helps the open-source community thrive."
        color = "#a78bfa"
    else:
        badge = "🏠 Solo Explorer"
        desc = "Focusing on your own garden this year! A great foundation to build on before sharing with the world."
        color = "#8b949e"
        
    st.markdown(
        f"""
        <div class="glass-card" style="text-align: center; margin-bottom: 2rem; border-color: rgba(255,255,255,0.06) !important;">
            <p style="color: rgba(255,255,255,0.4); font-size: 1.05rem; text-transform: uppercase;
                      letter-spacing: 0.15em; margin-bottom: 0.5rem; font-weight: 600;">
                External Contributions
            </p>
            <h1 style="font-size: 6.5rem; font-weight: 800; background: linear-gradient(135deg, #ffffff, {color});
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0.25rem 0;
                        letter-spacing: -2.5px; line-height: 1;">
                {external_count}
            </h1>
            <div style="background: rgba(255, 255, 255, 0.05); color: {color}; padding: 0.4rem 1.2rem; border-radius: 20px; font-weight: 700; font-size: 1.05rem; border: 1px solid {color}40; display: inline-block; margin-top: 0.5rem; margin-bottom: 1rem;">
                {badge}
            </div>
            <p style="color: rgba(255, 255, 255, 0.85); font-size: 1.15rem; max-width: 500px; margin: 0.5rem auto 0 auto; line-height: 1.6;">
                {desc}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_habits_audit(stats: dict[str, Any]):
    """Slide 5.5 — Habits & Hygiene Audit."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #ffffff; font-weight: 700; font-size: 2rem; letter-spacing: -0.5px;">Habits & Hygiene Audit</h2>
            <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem;">Tailored recommendations to elevate your workflow hygiene</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    recommendations = stats.get("recommendations", [])
    
    if recommendations:
        rec_html = '<div style="display: flex; flex-direction: column; gap: 1rem; margin-top: 1.5rem; margin-bottom: 2rem;">'
        for idx, rec in enumerate(recommendations):
            rec_clean = html.escape(str(rec))
            rec_html += f"""
            <div class="glass-card" style="display: flex; align-items: flex-start; gap: 1rem; border-color: rgba(255,255,255,0.06) !important; padding: 1.25rem 1.5rem !important;">
                <div style="background: rgba(255, 255, 255, 0.05); color: #ffffff; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; border: 1px solid rgba(255,255,255,0.1);">
                    {idx + 1}
                </div>
                <div style="color: rgba(255, 255, 255, 0.9); font-size: 1.05rem; line-height: 1.5; padding-top: 0.2rem;">
                    {rec_clean}
                </div>
            </div>
            """
        rec_html += "</div>"
        render_html_clean(rec_html)
    else:
        st.info("Everything looks clean! Your repo hygiene is outstanding. 🌟")
