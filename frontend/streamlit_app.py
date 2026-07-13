"""
GitHub Wrapped — Streamlit Frontend

A step-by-step "Spotify Wrapped"-style reveal of your GitHub year.
Communicates with the FastAPI backend to fetch stats and render slides.
"""

import base64
import os
from pathlib import Path

import httpx
import streamlit as st

# ── Must be the first Streamlit call ─────────────────────────────────────────
st.set_page_config(
    page_title="GitHub Wrapped",
    page_icon="🎁",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Import slides AFTER set_page_config
from components.slides import (
    render_commits_headline,
    render_heatmap,
    render_landing,
    render_languages,
    render_personality,
    render_share,
    render_streaks,
    render_chrono_type,
    render_coder_mood,
    render_battle_faceoff,
    render_battle_stats_duel,
    render_battle_verdict,
    render_frameworks_stack,
    render_open_source_impact,
    render_habits_audit,
)

# ── Config ───────────────────────────────────────────────────────────────────

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

# ── Load background image ───────────────────────────────────────────────────

def get_base64_image(image_filename: str) -> str:
    current_dir = Path(__file__).parent
    image_path = current_dir / image_filename
    if image_path.exists():
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

bg_base64 = get_base64_image("chrome_glass_bg.png")

# ── Custom CSS (Glassmorphism Mockup theme) ──────────────────────────────────

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* ── Global Typography & Layout ── */
    html, body, [data-testid="stAppViewContainer"], * {{
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }}

    /* ── Wallpaper Background with 3D Chrome ── */
    .stApp {{
        background-image: url("data:image/png;base64,{bg_base64}") !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
        background-color: #05070a !important;
    }}
    
    [data-testid="stHeader"] {{
        display: none !important;
    }}
    
    [data-testid="stSidebar"] {{
        background: rgba(18, 18, 18, 0.4) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }}

    /* ── Glass Window Container (.block-container) ── */
    .block-container {{
        background: rgba(18, 18, 18, 0.45) !important;
        backdrop-filter: blur(30px) saturate(145%) !important;
        -webkit-backdrop-filter: blur(30px) saturate(145%) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.22) !important;
        border-radius: 24px !important;
        padding: 0 2.5rem 2.5rem 2.5rem !important; /* Touch top flush */
        box-shadow: 0 35px 70px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        max-width: 720px !important;
        margin: 4.5rem auto !important;
        position: relative !important;
    }}

    /* ── Mockup OS/Browser Window Header ── */
    .window-controls-container {{
        position: relative !important;
        margin: 0 -2.5rem 2rem -2.5rem !important; /* Bleeds to side borders and creates natural bottom gap */
        height: 55px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 0 1.5rem !important;
        background: rgba(10, 10, 10, 0.15) !important;
        border-top-left-radius: 24px !important;
        border-top-right-radius: 24px !important;
    }}
    .window-controls {{
        display: flex !important;
        gap: 8px !important;
        align-items: center !important;
    }}
    .window-controls .dot {{
        width: 12px !important;
        height: 12px !important;
        border-radius: 50% !important;
        display: inline-block !important;
    }}
    .window-controls .dot.red {{ background-color: #ff5f56 !important; }}
    .window-controls .dot.yellow {{ background-color: #ffbd2e !important; }}
    .window-controls .dot.green {{ background-color: #27c93f !important; }}
    
    .window-url {{
        font-family: monospace !important;
        letter-spacing: 0.5px !important;
        color: rgba(255, 255, 255, 0.3) !important;
        font-size: 0.85rem !important;
    }}
    .window-menu {{
        display: flex !important;
        gap: 1.25rem !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        letter-spacing: 1px !important;
    }}
    .window-menu span {{
        color: rgba(255, 255, 255, 0.4) !important;
        transition: color 0.2s ease !important;
    }}
    .window-menu span.active {{
        color: #ffffff !important;
    }}

    /* ── Metric Cards inside Glass ── */
    [data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 16px !important;
        padding: 1.1rem !important;
        text-align: center !important;
        transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), 
                    border-color 0.3s ease !important;
    }}
    [data-testid="stMetric"]:hover {{
        transform: translateY(-3px) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
    }}
    [data-testid="stMetricValue"] {{
        color: #ffffff !important;
        font-size: 2.1rem !important;
        font-weight: 700 !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: rgba(255, 255, 255, 0.45) !important;
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* ── Sub-card dividers inside layout ── */
    .glass-card {{
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 16px !important;
        padding: 1.75rem !important;
        margin: 1.25rem 0 !important;
    }}

    /* ── Minimalist Inputs ── */
    .stTextInput > div > div > input {{
        background: rgba(255, 255, 255, 0.04) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        transition: border-color 0.25s ease, background 0.25s ease !important;
    }}
    .stSelectbox > div > div {{
        background: rgba(255, 255, 255, 0.04) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        transition: border-color 0.25s ease, background 0.25s ease !important;
    }}
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within {{
        border-color: rgba(255, 255, 255, 0.25) !important;
        background: rgba(255, 255, 255, 0.07) !important;
        box-shadow: none !important;
    }}

    /* ── UI Buttons ── */
    .stButton > button[kind="primary"] {{
        background: rgba(255, 255, 255, 0.9) !important;
        color: #0b0d13 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.65rem 1.75rem !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        transition: transform 0.2s ease, background 0.2s ease !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        transform: translateY(-2px) !important;
        background: #ffffff !important;
    }}
    .stButton > button[kind="secondary"] {{
        background: rgba(255, 255, 255, 0.05) !important;
        color: rgba(255, 255, 255, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        transition: background 0.2s ease, border-color 0.2s ease !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        background: rgba(255, 255, 255, 0.09) !important;
        border-color: rgba(255, 255, 255, 0.18) !important;
        color: #ffffff !important;
    }}

    /* ── Progress bar gradient ── */
    .stProgress > div > div > div {{
        background: rgba(255, 255, 255, 0.8) !important;
    }}

    /* ── Slide dots navigation ── */
    .slide-nav {{
        display: flex;
        justify-content: center;
        gap: 0.6rem;
        padding: 1.25rem 0;
    }}
    .slide-nav .dot {{
        width: 10px; height: 10px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.15);
        display: inline-block;
        transition: all 0.3s ease;
    }}
    .slide-nav .dot.active {{
        background: #ffffff !important;
        width: 26px;
        border-radius: 5px;
    }}

    /* ── Hide Streamlit Deploy, Menu and Footer ── */
    .stDeployButton, .stAppDeployButton, [data-testid="stDeployButton"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    #MainMenu, [data-testid="stIconMainMenu"], [data-testid="stConnectionStatus"] {{
        visibility: hidden !important;
        display: none !important;
    }}
    footer {{
        visibility: hidden !important;
        display: none !important;
    }}

    /* ── Slide Transitions & Smooth Animations ── */
    @keyframes slideUpFade {{
        0% {{
            opacity: 0;
            transform: translateY(16px);
        }}
        100% {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    /* Global Transition Defaults */
    h1, h2, h3, p, .glass-card, [data-testid="stMetric"], .stPlotlyChart, li, table, .slide-nav {{
        animation: slideUpFade 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
    }}

    /* Stagger Delays for Cascade Vibe */
    p {{
        animation-delay: 40ms !important;
    }}
    .glass-card, [data-testid="stMetric"] {{
        animation-delay: 80ms !important;
    }}
    .stPlotlyChart, li, table {{
        animation-delay: 120ms !important;
    }}
    .slide-nav {{
        animation-delay: 160ms !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state ────────────────────────────────────────────────────────────

if "slide" not in st.session_state:
    st.session_state.slide = 0
if "stats" not in st.session_state:
    st.session_state.stats = None
if "error" not in st.session_state:
    st.session_state.error = None
if "mode" not in st.session_state:
    st.session_state.mode = "solo"
if "battle_stats_1" not in st.session_state:
    st.session_state.battle_stats_1 = None
if "battle_stats_2" not in st.session_state:
    st.session_state.battle_stats_2 = None


def get_total_slides():
    return 4 if st.session_state.mode == "battle" else 12


def _fetch_wrapped(username: str, token: str, year: int) -> dict | None:
    """Call the backend API synchronously (Streamlit doesn't natively support async)."""
    try:
        with httpx.Client(timeout=30.0) as client:
            payload = {"username": username, "year": year}
            if token:
                payload["github_token"] = token

            resp = client.post(f"{API_BASE}/api/wrapped", json=payload)

            if resp.status_code != 200:
                detail = resp.json().get("detail", resp.text)
                st.session_state.error = f"API Error ({resp.status_code}): {detail}"
                return None

            return resp.json()

    except httpx.TimeoutException:
        st.session_state.error = "Request timed out. Please try again."
        return None
    except httpx.ConnectError:
        st.session_state.error = (
            "Could not connect to the backend. "
            "Make sure the FastAPI server is running on " + API_BASE
        )
        return None


# ── Navigation dots ──────────────────────────────────────────────────────────

def _render_nav_dots():
    """Show navigation dots for the current slide."""
    if st.session_state.slide == 0:
        return  # No dots on landing

    dots_html = '<div class="slide-nav">'
    for i in range(1, get_total_slides()):
        active = "active" if i == st.session_state.slide else ""
        dots_html += f'<span class="dot {active}"></span>'
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)


# ── Main flow ────────────────────────────────────────────────────────────────

def main():
    # Inject Mock Browser/OS window header
    user_badge = ""
    slide = st.session_state.slide
    stats = st.session_state.stats

    if st.session_state.mode == "battle" and st.session_state.battle_stats_1 and st.session_state.battle_stats_2:
        user_badge = f"@{st.session_state.battle_stats_1['username']} vs @{st.session_state.battle_stats_2['username']}"
    elif stats and "username" in stats:
        user_badge = f"@{stats['username']}"
    else:
        user_badge = "RECAP"

    st.markdown(
        f"""
        <div class="window-controls-container">
            <div class="window-controls">
                <span class="dot red"></span>
                <span class="dot yellow"></span>
                <span class="dot green"></span>
            </div>
            <div class="window-url">github-wrapped.com</div>
            <div class="window-menu">
                <span class="active">{user_badge}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if slide == 0:
        # Mode selector styling
        st.markdown(
            """
            <style>
            /* Customize segment buttons */
            div[data-testid="stHorizontalBlock"] {
                justify-content: center !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        
        # Pill selector at the top of the card
        mode_select = st.radio(
            "Select recap mode:",
            options=["Solo Recap 👤", "Versus Battle ⚔️"],
            horizontal=True,
            label_visibility="collapsed",
            key="app_mode_select",
        )
        
        st.session_state.mode = "battle" if "Versus" in mode_select else "solo"

        if st.session_state.mode == "solo":
            username, token, year, generate = render_landing()

            if generate:
                if not username:
                    st.error("Please enter a GitHub username.")
                else:
                    with st.spinner("🔍 Fetching your GitHub data..."):
                        result = _fetch_wrapped(username, token, year)
                        if result:
                            st.session_state.stats = result
                            st.session_state.error = None
                            st.session_state.slide = 1
                            st.rerun()
        else:
            # Battle Mode Landing page
            st.markdown(
                """
                <div style="text-align: center; margin-bottom: 1.5rem;">
                    <h1 style="color: #ffffff; font-weight: 800; font-size: 2.2rem; letter-spacing: -1px; margin-bottom: 0.25rem; line-height: 1.2;">
                        Versus Battle
                    </h1>
                    <p style="color: rgba(255, 255, 255, 0.45); font-size: 1.05rem; max-width: 600px; margin: 0.25rem auto 1rem auto;">
                        Compare the coding specs of two developers side-by-side.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                p1_username = st.text_input("Developer 1 Username", placeholder="e.g. torvalds", key="battle_p1")
            with col2:
                p2_username = st.text_input("Developer 2 Username", placeholder="e.g. gaearon", key="battle_p2")

            col_btn, col_yr = st.columns([2, 1])
            with col_yr:
                year = st.selectbox("Year", options=list(range(2025, 2007, -1)), index=0, key="battle_year")
            with col_btn:
                # Spacer
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                battle_generate = st.button("Start Battle ⚔️", use_container_width=True, type="primary")

            if battle_generate:
                if not p1_username or not p2_username:
                    st.error("Please enter both usernames.")
                else:
                    with st.spinner(f"⚔️ Fetching profiles and stats..."):
                        st.session_state.error = None
                        r1 = _fetch_wrapped(p1_username, None, year)
                        r2 = None
                        if r1:
                            r2 = _fetch_wrapped(p2_username, None, year)
                            
                        if r1 and r2:
                            st.session_state.battle_stats_1 = r1
                            st.session_state.battle_stats_2 = r2
                            st.session_state.slide = 1
                            st.rerun()

        if st.session_state.error:
            st.error(st.session_state.error)

    else:
        # ── Reveal slides ────────────────────────────────────────
        if st.session_state.mode == "solo":
            if stats is None:
                st.session_state.slide = 0
                st.rerun()
                return

            if slide == 1:
                render_commits_headline(stats)
            elif slide == 2:
                render_languages(stats)
            elif slide == 3:
                render_frameworks_stack(stats)
            elif slide == 4:
                render_chrono_type(stats)
            elif slide == 5:
                render_streaks(stats)
            elif slide == 6:
                render_heatmap(stats)
            elif slide == 7:
                render_open_source_impact(stats)
            elif slide == 8:
                render_coder_mood(stats)
            elif slide == 9:
                render_habits_audit(stats)
            elif slide == 10:
                render_personality(stats)
            elif slide == 11:
                render_share(stats, API_BASE)
        else:
            # Battle Mode reveal
            p1 = st.session_state.battle_stats_1
            p2 = st.session_state.battle_stats_2
            if p1 is None or p2 is None:
                st.session_state.slide = 0
                st.rerun()
                return

            if slide == 1:
                render_battle_faceoff(p1, p2)
            elif slide == 2:
                render_battle_stats_duel(p1, p2)
            elif slide == 3:
                render_battle_verdict(p1, p2)

        # ── Navigation dots (moved to bottom) ────────────────────
        _render_nav_dots()

        # ── Prev / Next buttons ──────────────────────────────────
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if slide > 1:
                if st.button("◀  Back", key="btn_back"):
                    st.session_state.slide -= 1
                    st.rerun()
            elif slide == 1:
                if st.button("🏠  Start Over", key="btn_home"):
                    st.session_state.slide = 0
                    st.session_state.stats = None
                    st.session_state.battle_stats_1 = None
                    st.session_state.battle_stats_2 = None
                    st.rerun()

        with col3:
            if slide < get_total_slides() - 1:
                if st.button("Next  ▶", key="btn_next", type="primary"):
                    st.session_state.slide += 1
                    st.rerun()


if __name__ == "__main__":
    main()


