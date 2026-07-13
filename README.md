# 🎁 GitHub Wrapped

**AI-powered, shareable GitHub activity recap** — think Spotify Wrapped, but for your code.

Enter your GitHub username and get a beautiful step-by-step reveal of your year: commits, top languages, streaks, contribution heatmaps, and an AI-generated coding personality blurb.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Commit headlines** | Total commits, stars, repos, PRs at a glance |
| **Language breakdown** | Interactive donut chart of your top 5 languages |
| **Tech Stack Frameworks** | Detects framework integrations (React, FastAPI, Docker) from repo topics & descriptions |
| **Developer Chrono-Type** | Captures a 24-hour circular activity timeline from push event logs |
| **Streak analysis** | Longest and current coding streaks |
| **Contribution heatmap** | GitHub-style calendar (uses GraphQL with PAT, falls back to unauthenticated public HTML scraping if PAT is missing) |
| **Open-Source Impact** | Tallies public event contributions made to external repositories |
| **Coder Mood & AI Roast** | Assigns a coding vibe and generates a sharp commit-based AI roast |
| **Habits & Hygiene Audit** | Scans repositories for license missing flags, repository descriptions, and commit hygiene |
| **AI personality** | Fun coding persona summaries via HuggingFace (with rule-based fallback) |
| **Versus Battle Mode** | Head-to-head matchup comparison of two developers |
| **Profile README Card** | Generates copy-pasteable Markdown summarizing yearly stats |
| **Shareable PNG card** | Download a dark-themed card with all your stats |
| **Rate-limited & cached** | slowapi rate-limiting + in-memory TTL cache |

---

## 🏗 Architecture

```
┌─────────────────┐         ┌──────────────────────┐
│   Streamlit UI  │ ──HTTP──▶  FastAPI Backend     │
│   (port 8501)   │         │  (port 8000)          │
└─────────────────┘         │                      │
                            │  ┌─ github_service   │──▶ GitHub REST + GraphQL
                            │  ├─ stats_engine     │
                            │  ├─ ai_service       │──▶ HuggingFace API
                            │  └─ image_service    │    (Pillow PNG renderer)
                            └──────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- (Optional) A GitHub Personal Access Token (PAT). If no PAT is provided, the application automatically scrapes the user's public contributions calendar page to populate commit counts, streaks, and heatmap data.
- (Optional) A HuggingFace API token for AI personality summaries

### 1. Clone & install

```bash
git clone https://github.com/yourname/github-wrapped.git
cd github-wrapped

# Backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r backend/requirements.txt

# Frontend (separate terminal)
pip install -r frontend/requirements.txt
```

### 2. Configure environment

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

Open http://localhost:8501 in your browser 🎉

### Docker (alternative)

```bash
docker compose up --build
```

---

## 🧪 Running Tests

```bash
pip install pytest
pytest backend/tests/ -v
```

---

## 📁 Project Structure

```
Wrapped/
├── backend/
│   ├── app/
│   │   ├── core/          # config, cache, security
│   │   ├── models/        # Pydantic schemas
│   │   ├── routers/       # API endpoints
│   │   └── services/      # github, stats, ai, image
│   ├── tests/             # pytest unit tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── components/        # slides, charts
│   ├── streamlit_app.py
│   ├── Dockerfile
│   └── requirements.txt
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .env.example
├── LICENSE (MIT)
└── README.md
```

---

## 📄 License

MIT — see [LICENSE](LICENSE).
