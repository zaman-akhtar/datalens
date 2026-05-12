# DataLens — Spring 2026 Final Project

> Upload any CSV → see an auto-generated dashboard, filter it interactively, ask questions in chat, get an executive summary.
> Course: **Generative AI for Business** (Spring 2026). Assigned dataset: **Dataset 6 — Credit Card Transactions** (Kaggle, 1.29 M rows).

## Team

- **Member 1:** Zaman Akhtar (22i-0746)
- **Member 2:** Azan Shafique (22i-0669)
- **Member 3:** Alizay Rasheed (22i-0670)
- **Assigned Dataset:** Dataset 6 — Credit Card Transactions

## What DataLens does

DataLens turns a raw CSV into a usable analytics surface in under a minute. Drag a file in, the backend profiles every column, the frontend renders 4–6 visualizations chosen automatically from the data shape, a global filter bar updates every chart at once, an LLM-powered chat answers plain-English questions by calling Python tools that query the data, and a one-paragraph executive summary surfaces the headline numbers — all without writing a line of SQL or a single chart specification.

The application logic is **dataset-agnostic**: nothing in `backend/app/` or `frontend/src/` references credit-card columns by name. The same code works on any of the 20 roster CSVs.

## Prerequisites

- **Python 3.11+** — https://www.python.org/downloads/
- **Node.js 20+** — https://nodejs.org/
- **uv** (Python package manager) —
  - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Git** — https://git-scm.com/

## LLM API key

DataLens defaults to **Google Gemini 1.5 Flash** (free tier, see ADR-001). Get a key at https://aistudio.google.com/apikey — no credit card needed.

If Gemini is rate-limited the day of the demo, you can swap to OpenAI by changing `LLM_PROVIDER=openai` in `.env` and pasting an `OPENAI_API_KEY`.

## Setup

```bash
# 1. Clone
git clone https://github.com/zaman-akhtar/datalens.git
cd datalens

# 2. Configure environment
cp .env.example .env
# Open .env and paste your GEMINI_API_KEY

# 3. Install backend deps
cd backend && uv sync && cd ..

# 4. Install frontend deps
cd frontend && npm install && cd ..
```

## Run

Two terminals:

```bash
# Terminal 1 — backend
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

…or one terminal:

```bash
# From repo root
npm run dev:all
```

Open http://localhost:5173.

## Quickstart with the assigned dataset

The full Kaggle file is 338 MB — above DataLens's 50 MB upload cap (see SPEC §8 for the rationale). A 50,000-row sample ships in `data/credit_card_transactions_sample_50k.csv` (~14 MB). Drag that file into the upload zone; the dashboard renders within ~15 seconds.

Try these chat questions:

- *"Which category has the highest fraud rate?"*
- *"What does the amt column look like — show me a histogram."*
- *"How does transaction volume change by hour of day?"*
- *"Which states contribute the most fraudulent dollars?"*

To swap to a completely different dataset (proves DataLens is not credit-card-specific), upload any other Kaggle CSV — the dashboard regenerates from scratch.

## Tests

```bash
# Backend (pytest, ≥ 14 tests — actually 53 across the suite)
cd backend && uv run pytest -v

# Frontend components (Vitest, ≥ 7 tests — actually 27)
cd frontend && npm run test

# End-to-end (Playwright — the 40-pt rubric suite). Requires both servers running.
cd frontend && npm run test:e2e

# Run everything in sequence
npm run test:all
```

## Linting and formatting

```bash
# Python
cd backend && uv run ruff check . && uv run ruff format --check .

# TypeScript / React
cd frontend && npm run lint && npm run format:check
```

## Troubleshooting

**Port 8000 or 5173 already in use**
- macOS / Linux: `lsof -i :8000` then `kill -9 <PID>`
- Windows: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`

**`uv: command not found`**
Re-run the uv installer from Prerequisites; restart your shell.

**Gemini returns 429 / rate-limited**
Wait 60 seconds and retry, or swap providers in `.env`. The dashboard, filters, profile, and cached summary keep working — only the chat panel goes idle.

**CSV upload returns 413**
Your file is over 50 MB. Use the supplied 50 k sample, or generate a smaller sample with `python scripts/make_sample.py path/to/your.csv 50000`.

**Frontend says "Failed to fetch /api/…" while backend is running**
Check that `CORS_ORIGINS` in `.env` includes `http://localhost:5173`.

**Chat panel shows "AI is rate-limited"**
Same as the Gemini 429 case above. You can also set `MOCK_LLM=1` in `.env` to use a deterministic fake provider for demos.

## Project structure

```
.
├── .agent/skills/          # 6 mandatory skills (DO NOT MODIFY — graded as-is)
├── data/                   # bundled dev sample CSV
├── docs/
│   ├── adrs/               # Architecture Decision Records (ADR-001..003)
│   ├── dataset-analysis.md # empirical notes on the assigned CSV
│   ├── system-design.md    # API map, LLM tools, components
│   ├── test-strategy.md    # pytest + Vitest + Playwright plan
│   ├── risks.md            # top-5 risks with mitigations
│   └── report.md           # final reflection (graded artifact)
├── tasks/
│   ├── plan.md             # 7 implementation phases
│   └── todo.md             # ~33 atomic tasks
├── backend/                # FastAPI + Pydantic + Pandas + SQLite
├── frontend/               # React + Vite + Tailwind + Recharts
├── SPEC.md                 # the spec (10 sections)
├── README.md               # this file
├── .env.example            # environment template
└── pyproject.toml          # Python project metadata
```

## Contribution summary

- **Zaman Akhtar:** project direction, SPEC.md, ADRs, dataset analysis, backend implementation, frontend implementation, demo planning.
- **Azan Shafique:** requirements review, dataset research, testing feedback, documentation review.
- **Alizay Rasheed:** requirements review, dataset research, testing feedback, documentation review.

## Acknowledgments

Built for the Spring 2026 *Generative AI for Business* course. Coding agent: **Claude (Cowork)**. Agent Skills framework by Addy Osmani — MIT licensed, https://github.com/addyosmani/agent-skills. Dataset: *Credit Card Transactions* by Priyam Choksi on Kaggle — https://www.kaggle.com/datasets/priyamchoksi/credit-card-transactions-dataset.

## License

MIT.
