<div align="center">

# 🎁 GitHub Wrapped

**Your year in code — beautifully visualized.**

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-app--wrapped.streamlit.app-FF4B4B?style=for-the-badge)](https://app-wrapped.streamlit.app)
[![CI](https://img.shields.io/github/actions/workflow/status/soumainchoudhary/github-wrapped/ci.yml?branch=main&style=for-the-badge&label=CI)](https://github.com/soumainchoudhary/github-wrapped/actions)
[![License](https://img.shields.io/github/license/soumainchoudhary/github-wrapped?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

*Think Spotify Wrapped, but for your GitHub.*  
Enter any public GitHub username and get a stunning, slide-by-slide recap of your developer year — commits, languages, streaks, AI personality, and more. **No login required.**

[**Try it now →**](https://app-wrapped.streamlit.app)

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Commit Headlines** | Total commits, stars, repos, and PRs at a glance |
| 🍩 **Language Breakdown** | Interactive donut chart of your top 5 languages |
| ⚡ **Tech Stack Detection** | Auto-detects frameworks (React, FastAPI, Docker) from repo topics & descriptions |
| 🕐 **Developer Chrono-Type** | 24-hour circular activity radar from push event timestamps |
| 🔥 **Streak Analysis** | Longest and current coding streaks with visual charts |
| 📅 **Contribution Heatmap** | GitHub-style calendar built from public contribution data |
| 🌍 **Open-Source Impact** | Tallies contributions made to external repositories |
| 🎭 **Coder Mood & AI Roast** | Assigns a coding vibe and generates a witty AI roast |
| 🧹 **Habits & Hygiene Audit** | Scans repos for missing licenses, descriptions, and commit hygiene |
| 🤖 **AI Personality** | Fun coding persona via HuggingFace (with rule-based fallback) |
| ⚔️ **Versus Battle Mode** | Head-to-head comparison of two developers |
| 📄 **Profile README Card** | Copy-pasteable Markdown summary of your yearly stats |
| 🎴 **Shareable PNG Card** | Download a premium dark-themed stats card |
| 🛡️ **Rate-Limited & Cached** | slowapi rate-limiting + in-memory TTL cache |

---

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────────┐
│   Streamlit UI  │ ──HTTP──▶  FastAPI Backend     │
│   (port 8501)   │         │  (port 8000)          │
└─────────────────┘         │                      │
                            │  ┌─ github_service   │──▶ GitHub Public REST API
                            │  ├─ stats_engine     │
                            │  ├─ ai_service       │──▶ HuggingFace Inference API
                            │  └─ image_service    │    (Pillow PNG renderer)
                            └──────────────────────┘
```

**Key design decisions:**
- 🔓 **Zero authentication required** — all data is fetched from GitHub's public APIs and contribution pages
- 🛡️ **XSS-hardened frontend** — all dynamic strings are `html.escape()`d before rendering
- ⚡ **Optimized API calls** — repo languages extracted from list objects (no per-repo API calls), capped pagination

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- (Optional) A [HuggingFace API token](https://huggingface.co/settings/tokens) for AI personality summaries

### 1. Clone & Install

```bash
git clone https://github.com/soumainchoudhary/github-wrapped.git
cd github-wrapped

# Backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r backend/requirements.txt

# Frontend (separate terminal)
pip install -r frontend/requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env and optionally add HF_API_TOKEN
```

### 3. Run

```bash
# Terminal 1 — Backend
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — Frontend
streamlit run frontend/streamlit_app.py
```

Open **http://localhost:8501** in your browser 🎉

### Docker (Alternative)

```bash
docker compose up --build
```

---

## 🧪 Tests

```bash
python -m pytest backend/tests/ -v
```

All 35 tests cover the stats engine, AI service fallbacks, and API endpoint validation.

---

## 🌐 Deployment

This project is deployed as a split architecture:

| Service | Platform | URL |
|---|---|---|
| **Frontend** | Streamlit Community Cloud | [app-wrapped.streamlit.app](https://app-wrapped.streamlit.app) |
| **Backend** | Render (Free Tier) | Deployed as a Docker web service |

> **Note:** On the free tier, the Render backend may take ~60 seconds to wake up on first use after 15 minutes of inactivity.

---

## 📁 Project Structure

```
github-wrapped/
├── backend/
│   ├── app/
│   │   ├── core/              # config, cache, rate-limiting
│   │   ├── models/            # Pydantic schemas & validation
│   │   ├── routers/           # API endpoints
│   │   └── services/          # github, stats, ai, image
│   ├── tests/                 # 35 pytest unit tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── components/            # slide renderers, chart builders
│   ├── streamlit_app.py       # main app entrypoint
│   ├── Dockerfile
│   └── requirements.txt
├── .github/workflows/ci.yml   # lint (ruff) + test + docker build
├── docker-compose.yml
├── .env.example
├── LICENSE (MIT)
└── README.md
```

---

## 🛠️ Tech Stack

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat-square&logo=plotly&logoColor=white)
![Pillow](https://img.shields.io/badge/Pillow-3776AB?style=flat-square&logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)

</div>

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

**Built with ❤️ by [Soumain Choudhary](https://github.com/soumainchoudhary)**

*If you found this useful, consider giving it a ⭐!*

</div>
