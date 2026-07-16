"""
Image service — renders a shareable PNG card with Pillow.

The card uses a glassmorphic visual style with:
  • Background wallpaper backdrop matching the app
  • Semi-transparent glass panels with thin bright borders
  • Stylish default typography (Segoe UI/Arial)
  • Key stats, language bars, and AI personality recap
"""

from __future__ import annotations

import io
import os

from PIL import Image, ImageDraw, ImageFont

from backend.app.models.schemas import WrappedStats

# ── Dimensions and Glassmorphic Theme Color Palette ────────────────────────
CARD_WIDTH = 1080
CARD_HEIGHT = 1620

# Glass panel fills and borders (with alpha)
GLASS_BG = (10, 12, 18, 215)       # Darker translucent card fill for high contrast
GLASS_BORDER = (255, 255, 255, 55)  # Thin white border highlight
PANEL_BG = (255, 255, 255, 15)      # Inner stat block fill
PANEL_BORDER = (255, 255, 255, 30)

ACCENT = (139, 92, 246)            # Purple #8b5cf6
ACCENT_CYAN = (56, 189, 248)       # Cyan #38bdf8
TEXT_PRIMARY = (255, 255, 255)     # #ffffff
TEXT_SECONDARY = (180, 190, 200)   # Light gray for secondary text

# Language colors
LANG_COLORS = {
    "Python": (53, 114, 165),
    "JavaScript": (241, 224, 90),
    "TypeScript": (49, 120, 198),
    "Java": (176, 114, 25),
    "Go": (0, 173, 216),
    "Rust": (222, 165, 132),
    "C++": (243, 75, 125),
    "Ruby": (112, 21, 22),
    "PHP": (79, 93, 149),
    "Swift": (240, 81, 56),
}


def clean_text_for_pillow(text: str) -> str:
    """Filter out emojis and non-supported symbols to prevent rendering box character errors."""
    return "".join(c for c in text if ord(c) < 0x2000).strip()


def _get_background_image() -> Image.Image:
    """Load the project's background wallpaper or render a premium fallback gradient."""
    paths = [
        "frontend/chrome_glass_bg.png",
        "../frontend/chrome_glass_bg.png",
        "chrome_glass_bg.png",
        "/app/frontend/chrome_glass_bg.png"
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                bg = Image.open(p)
                return bg.resize((CARD_WIDTH, CARD_HEIGHT))
            except Exception:
                pass
                
    # Fallback premium dark gradient
    img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), (13, 17, 23))
    draw = ImageDraw.Draw(img)
    for y in range(CARD_HEIGHT):
        r = int(10 + (y / CARD_HEIGHT) * 15)
        g = int(12 + (y / CARD_HEIGHT) * 15)
        b = int(18 + (y / CARD_HEIGHT) * 22)
        draw.line([(0, y), (CARD_WIDTH, y)], fill=(r, g, b))
    return img


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try to load Segoe UI, then Arial, falling back to default."""
    font_names = (
        ["segoeuib.ttf", "arialbd.ttf", "Arial Bold.ttf"] if bold
        else ["segoeui.ttf", "arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]
    )
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def render_card(stats: WrappedStats) -> bytes:
    """Render the Wrapped stats card with glassmorphism overlays and return PNG bytes."""
    # 1. Base image setup and darkening
    base_img = _get_background_image().convert("RGBA")
    
    # Apply a dark tint overlay directly to the background to ensure high readability
    dark_tint = Image.new("RGBA", base_img.size, (10, 12, 18, 180)) # Very dark overlay
    base_img = Image.alpha_composite(base_img, dark_tint)
    
    # 2. Overlay container for alpha drawing
    overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # 3. Load Fonts
    font_title = _get_font(56, bold=True)
    font_subtitle = _get_font(32, bold=True)
    font_stat_big = _get_font(64, bold=True)
    font_stat_label = _get_font(24)
    font_body = _get_font(26)
    font_brand = _get_font(22)
    font_lang = _get_font(24)

    # ── Main Card Border Container ──────────────────────────────────
    draw.rounded_rectangle(
        (30, 30, CARD_WIDTH - 30, CARD_HEIGHT - 30),
        radius=28,
        fill=GLASS_BG,
        outline=GLASS_BORDER,
        width=2
    )

    # ── Avatar Circle ───────────────────────────────────────────────
    avatar_cx, avatar_cy = 540, 140
    avatar_r = 60
    draw.ellipse(
        (avatar_cx - avatar_r, avatar_cy - avatar_r,
         avatar_cx + avatar_r, avatar_cy + avatar_r),
        fill=(ACCENT[0], ACCENT[1], ACCENT[2], 200),
        outline=(255, 255, 255, 80),
        width=2
    )
    initials = clean_text_for_pillow(stats.username[:2].upper())
    draw.text(
        (avatar_cx, avatar_cy),
        initials,
        fill=TEXT_PRIMARY,
        font=_get_font(34, bold=True),
        anchor="mm"
    )

    # ── Header text ────────────────────────────────────────────────
    y = 225
    draw.text(
        (540, y),
        f"@{clean_text_for_pillow(stats.username)}",
        fill=TEXT_PRIMARY,
        font=font_title,
        anchor="mt"
    )
    y += 72
    draw.text(
        (540, y),
        f"GitHub Wrapped {stats.year}",
        fill=ACCENT_CYAN,
        font=font_subtitle,
        anchor="mt"
    )

    # ── Stats Grid Container (Increased spacing to prevent overlapping) ──
    y += 85
    draw.rounded_rectangle(
        (60, y - 15, CARD_WIDTH - 60, y + 285),
        radius=18,
        fill=PANEL_BG,
        outline=PANEL_BORDER,
        width=1
    )

    stats_data = [
        (str(stats.total_commits), "Commits"),
        (str(stats.total_stars), "Stars Earned"),
        (str(stats.total_repos), "Repositories"),
        (f"{stats.longest_streak_days}d", "Longest Streak"),
        (str(stats.total_prs), "Pull Requests"),
        (str(stats.total_issues), "Issues"),
    ]

    cols = [240, 540, 840]
    for i, (val, label) in enumerate(stats_data):
        row = i // 3
        col = i % 3
        cx = cols[col]
        cy = y + 10 + row * 140  # Spacing for larger fonts
        
        # Draw value
        draw.text((cx, cy), val, fill=TEXT_PRIMARY, font=font_stat_big, anchor="mt")
        # Draw label
        draw.text((cx, cy + 72), label, fill=TEXT_SECONDARY, font=font_stat_label, anchor="mt")

    # ── Languages Section ──────────────────────────────────────────
    y += 340  # Pushed down to clear the taller stats panel
    draw.text(
        (80, y),
        "Languages Stack",
        fill=TEXT_PRIMARY,
        font=font_subtitle
    )
    y += 55

    for i, lang in enumerate(stats.languages[:5]):
        lx = 100
        ly = y + i * 46
        
        # Color dot
        dot_color = LANG_COLORS.get(lang.name, (139, 148, 158))
        draw.ellipse(
            (lx, ly + 4, lx + 14, ly + 18),
            fill=(dot_color[0], dot_color[1], dot_color[2], 255)
        )
        # Text name
        draw.text(
            (lx + 24, ly),
            f"{clean_text_for_pillow(lang.name)}",
            fill=TEXT_PRIMARY,
            font=font_lang
        )
        # Percentage
        draw.text(
            (400, ly),
            f"{lang.percentage}%",
            fill=TEXT_SECONDARY,
            font=font_lang
        )
        # Bar track
        bar_x = 480
        bar_w = 480
        draw.rounded_rectangle(
            (bar_x, ly + 4, bar_x + bar_w, ly + 18),
            radius=7,
            fill=(255, 255, 255, 15)
        )
        # Bar fill
        bar_fill = int(bar_w * lang.percentage / 100)
        if bar_fill > 2:
            draw.rounded_rectangle(
                (bar_x, ly + 4, bar_x + bar_fill, ly + 18),
                radius=7,
                fill=(dot_color[0], dot_color[1], dot_color[2], 230)
            )

    # ── Activity Highlights Card (Cleaned of Emoji boxes) ──────────
    y += 275
    draw.rounded_rectangle(
        (60, y, CARD_WIDTH - 60, y + 100),
        radius=18,
        fill=PANEL_BG,
        outline=PANEL_BORDER,
        width=1
    )

    draw.text(
        (90, y + 16),
        f"Busiest Day: {stats.busiest_day_of_week}",
        fill=TEXT_PRIMARY,
        font=font_body
    )
    draw.text(
        (90, y + 48),
        f"Busiest Month: {stats.busiest_month}",
        fill=TEXT_PRIMARY,
        font=font_body
    )

    if stats.top_repo_name:
        repo_name_clean = clean_text_for_pillow(stats.top_repo_name)
        draw.text(
            (560, y + 16),
            f"Top Repo: {repo_name_clean}",
            fill=TEXT_PRIMARY,
            font=font_body
        )
        draw.text(
            (560, y + 48),
            f"{stats.top_repo_stars} stars  •  {stats.top_repo_language}",
            fill=TEXT_SECONDARY,
            font=font_body
        )

    # ── Personality Card (Cleaned of Emojis to prevent box errors) ──
    y += 140
    draw.rounded_rectangle(
        (60, y, CARD_WIDTH - 60, y + 140),
        radius=18,
        fill=(139, 92, 246, 25), # Subtle translucent purple
        outline=(139, 92, 246, 80),
        width=1
    )

    personality = stats.personality or "Your coding journey is just getting started!"
    personality_clean = clean_text_for_pillow(personality)
    _draw_wrapped_text(
        draw, personality_clean, font_body, TEXT_PRIMARY,
        x=90, y=y + 18, max_width=CARD_WIDTH - 180
    )

    # ── Brand Footer ────────────────────────────────────────────────
    draw.text(
        (540, CARD_HEIGHT - 65),
        "github-wrapped  •  Share your year in code",
        fill=TEXT_SECONDARY,
        font=font_brand,
        anchor="mt"
    )

    # 4. Composite drawing overlay onto base image
    final_img = Image.alpha_composite(base_img, overlay)
    
    # 5. Convert back to RGB and save
    rgb_img = final_img.convert("RGB")
    buf = io.BytesIO()
    rgb_img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, ...],
    x: int,
    y: int,
    max_width: int,
    line_spacing: int = 6,
) -> None:
    """Helper to draw wrapped lines of text on the canvas."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    for i, line in enumerate(lines[:4]):  # max 4 lines
        draw.text(
            (x, y + i * (font.size + line_spacing)),
            line,
            fill=fill,
            font=font,
        )
