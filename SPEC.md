# SPEC: DataLens

A web app that accepts ANY CSV, auto-profiles it, renders 4–6 visualizations on a filterable dashboard, hosts an LLM chat with tool use, and produces an executive summary. The application logic is dataset-agnostic; the assigned **Credit Card Transactions** dataset (1.29 M rows, 23 columns, 2019–2020) is the primary acceptance vehicle but never appears in code as a hardcoded assumption.

*Spec version: 1.0 | Last updated: 2026-05-04*

---

## 1. Objective

DataLens is a single-page web application that turns a raw CSV into a usable analytics surface in under one minute. A non-technical analyst uploads a file, sees an auto-generated dashboard of 4–6 visualizations chosen from the data shape, applies global filters that propagate to every chart, asks free-text questions in a chat panel that is answered by an LLM grounded through three tool calls, and reads a one-paragraph executive summary auto-written from the data.

**Target user — primary persona:** *Ananya, a junior fraud analyst at a regional bank.* She receives ad-hoc CSV exports from the data team, has never written SQL, lives in Excel, and needs to triage a new file in 5 minutes before her standup. She measures success in "did I find the anomaly before the meeting started." DataLens replaces the 30-minute Pandas notebook a colleague would otherwise write for her.

**Success — testable:**
- Ananya uploads a 14 MB CSV and sees the dashboard render within **15 seconds** end-to-end.
- The dashboard contains **at least 4 and at most 6** visualizations chosen automatically.
- Selecting one filter value (e.g. `state = NY`) updates **every chart** in **< 500 ms** measured from filter onChange to last paint.
- A natural-language question ("which category has the highest fraud rate?") returns an answer in **< 10 seconds** with a citation back to the table or chart it queried.
- The executive summary generates in **< 30 seconds** of upload completion and contains **at least 3 numeric facts pulled from the data** (verified by regex check in the Playwright suite).
- Uploading a different CSV (e.g. a hotel-booking file) replaces the dataset cleanly with no application restart and no leakage of credit-card-specific terms.

### User stories

1. *As a fraud analyst*, I want to upload a CSV and see a dashboard within 15 seconds, so that I can triage a new dataset before my standup.
2. *As a fraud analyst*, I want to filter every chart at once by category, state, or date range, so that I can isolate suspicious slices without rebuilding charts.
3. *As a fraud analyst*, I want to ask plain-English questions and get a numeric answer with the SQL it ran, so that I can trust the result and re-use the query.
4. *As a fraud analyst*, I want an auto-generated executive summary I can paste into Slack, so that I can share findings with my manager in two clicks.
5. *As a course grader*, I want to upload a different CSV from the dataset roster and see the same flow work, so that I can verify dataset-agnostic behavior in the live demo.

### Assumptions

1. The user has a single CSV under 50 MB. (Larger files use the dev sample workflow documented in README.)
2. The CSV has a header row in the first row.
3. UTF-8 encoding (Latin-1 fallback documented but not in MVP).
4. The user runs DataLens locally — no auth, no multi-tenant.
5. The LLM provider (Google Gemini) is reachable and the free-tier quota is sufficient for a 30-minute demo.
6. The grader's machine has Python 3.11+, Node 20+, and `uv` installed (documented in README).
7. SQLite handles the dev sample (50 k rows) with full-table scans in < 100 ms — verified, not assumed.
8. Recharts can render 4 simultaneous charts with up to 50 categorical bins each at 60 fps on a typical laptop — verified in Phase 3.

---

## 2. Tech Stack

Locked by the project rubric. Concrete library choices below; rationale lives in ADRs 001–003.

| Layer | Choice | Version |
|---|---|---|
| Frontend framework | React + Vite | React 18.3, Vite 5.x |
| Styling | Tailwind CSS | 3.4 |
| UI primitives | shadcn/ui (Radix under the hood) | latest |
| Chart library | **Recharts** (ADR-002) | 2.12 |
| Frontend testing | Vitest + React Testing Library | latest |
| E2E testing | Playwright | 1.45+ |
| Backend framework | FastAPI | 0.111 |
| Data validation | Pydantic v2 | 2.7 |
| Python | 3.11+ | — |
| Package manager (Python) | `uv` + `pyproject.toml` | latest |
| Data processing | Pandas | 2.2 |
| Database | SQLite | bundled |
| Backend testing | pytest + httpx | pytest 8, httpx 0.27 |
| LLM provider | **Google Gemini 1.5 Flash** (ADR-001) | `google-generativeai` SDK |
| LLM integration pattern | Tool-use / function calling | per Gemini SDK |
| Coding agent | Claude (Cowork) | — |
| Backend port | 8000 | — |
| Frontend port | 5173 | — |

---

## 3. Commands

All commands run from the repo root. Cross-platform; verified on macOS and Windows (PowerShell).

```
Setup (once):
  cd backend && uv sync
  cd frontend && npm install
  cp .env.example .env   # then paste GEMINI_API_KEY

Dev (two terminals, or use the helper):
  Terminal 1:  cd backend  && uv run uvicorn app.main:app --reload --port 8000
  Terminal 2:  cd frontend && npm run dev   # serves on http://localhost:5173
  Helper:      npm run dev:all              # tmux/concurrently both at once

Test:
  Backend:     cd backend  && uv run pytest -v
  Frontend:    cd frontend && npm run test
  E2E:         cd frontend && npm run test:e2e   # Playwright, requires both servers running
  All:         npm run test:all                  # runs the three above sequentially

Lint / Format:
  Backend:     cd backend  && uv run ruff check . && uv run ruff format --check .
  Frontend:    cd frontend && npm run lint && npm run format:check

Build (production frontend bundle):
  cd frontend && npm run build  # outputs to frontend/dist/
```

---

## 4. Project Structure

```
.
├── .agent/skills/                         → 6 mandatory skills (DO NOT MODIFY)
├── data/
│   └── credit_card_transactions_sample_50k.csv   → dev sample, .gitignored above 1 MB
├── docs/
│   ├── adrs/
│   │   ├── 000-template.md
│   │   ├── 001-llm-provider.md
│   │   ├── 002-charting-library.md
│   │   └── 003-sqlite-schema-strategy.md
│   ├── dataset-analysis.md                → empirical notes on the assigned CSV
│   ├── system-design.md                   → API map, tool layer, component tree
│   ├── test-strategy.md                   → pytest + Vitest + Playwright plan
│   ├── risks.md                           → top 5 risks with mitigations
│   └── report.md                          → final reflection (graded artifact)
├── tasks/
│   ├── plan.md                            → 7 phases
│   └── todo.md                            → ~33 atomic tasks, ≤ 5 files each
├── backend/
│   ├── app/
│   │   ├── main.py                        → FastAPI entry, CORS, routers
│   │   ├── routers/
│   │   │   ├── upload.py                  → POST /api/upload
│   │   │   ├── profile.py                 → GET  /api/datasets/{id}/profile
│   │   │   ├── query.py                   → POST /api/datasets/{id}/query
│   │   │   ├── chat.py                    → POST /api/datasets/{id}/chat
│   │   │   └── summary.py                 → GET  /api/datasets/{id}/summary
│   │   ├── models/                        → Pydantic schemas (one file per resource)
│   │   ├── services/
│   │   │   ├── ingest.py                  → CSV → SQLite, type inference
│   │   │   ├── profile.py                 → null %, cardinality, skew, sample values
│   │   │   ├── chart_picker.py            → profile → 4-6 (chart_type, x, y)
│   │   │   ├── query_engine.py            → safe parametrized SELECT builder
│   │   │   ├── llm/
│   │   │   │   ├── provider.py            → Gemini wrapper, single point to swap
│   │   │   │   ├── tools.py               → query_data / get_column_statistics / generate_chart
│   │   │   │   └── summary_prompt.py
│   │   │   └── enrichment/
│   │   │       └── credit_cards.py        → optional dataset-aware hook (off by default)
│   │   └── db/
│   │       ├── session.py                 → SQLite connection
│   │       └── schema.py                  → datasets table + per-dataset dynamic table
│   └── tests/
│       ├── test_upload.py
│       ├── test_profile.py
│       ├── test_chart_picker.py
│       ├── test_query_engine.py
│       ├── test_llm_tools.py
│       └── fixtures/                      → small CSVs covering edge cases
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   └── Dashboard.tsx
│   │   ├── components/
│   │   │   ├── UploadDropzone.tsx
│   │   │   ├── ProfileCard.tsx
│   │   │   ├── ChartGrid.tsx
│   │   │   ├── chart/{BarChart,LineChart,Histogram,ScatterChart,KPI}.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   ├── ChatPanel.tsx
│   │   │   └── ExecutiveSummary.tsx
│   │   ├── hooks/
│   │   │   ├── useDataset.ts
│   │   │   └── useFilters.ts              → Zustand store
│   │   └── lib/
│   │       └── api.ts                     → typed fetch client
│   └── tests/
│       ├── ChartGrid.test.tsx
│       ├── FilterBar.test.tsx
│       ├── ChatPanel.test.tsx
│       ├── UploadDropzone.test.tsx
│       └── e2e/full-flow.spec.ts          → Playwright
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
└── SPEC.md
```

---

## 5. Code Style

**Naming**: `snake_case` Python; `camelCase` TS; `PascalCase` React components and Pydantic models. **Formatting**: `ruff format` (Python, line length 100), Prettier (TS/TSX). **Type hints**: required on every Python function — enforced by ruff `ANN` rules. **TypeScript**: strict mode on. **Comments**: explain *why*, not *what*.

### Sample Pydantic model (`backend/app/models/dataset.py`)

```python
from datetime import datetime
from pydantic import BaseModel, Field

class ColumnProfile(BaseModel):
    name: str
    dtype: str = Field(description="One of: numeric, categorical, datetime, boolean, text")
    null_pct: float = Field(ge=0.0, le=1.0)
    n_unique: int
    sample_values: list[str | int | float | None] = Field(max_length=5)

class DatasetProfile(BaseModel):
    dataset_id: str
    n_rows: int
    n_cols: int
    columns: list[ColumnProfile]
    created_at: datetime
```

### Sample FastAPI handler (`backend/app/routers/profile.py`)

```python
from fastapi import APIRouter, HTTPException
from app.models.dataset import DatasetProfile
from app.services.profile import build_profile

router = APIRouter(prefix="/api/datasets", tags=["profile"])

@router.get("/{dataset_id}/profile", response_model=DatasetProfile)
def get_profile(dataset_id: str) -> DatasetProfile:
    try:
        return build_profile(dataset_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found") from e
```

### Sample React component (`frontend/src/components/FilterBar.tsx`)

```tsx
import { useFilters } from "@/hooks/useFilters";
import type { ColumnProfile } from "@/lib/types";

interface FilterBarProps {
  columns: ColumnProfile[];
}

export function FilterBar({ columns }: FilterBarProps) {
  const { filters, setFilter, clear } = useFilters();
  const filterable = columns.filter((c) => c.dtype === "categorical" && c.n_unique <= 50);

  return (
    <div className="flex gap-2 flex-wrap p-2 bg-slate-50 rounded">
      {filterable.map((col) => (
        <select
          key={col.name}
          aria-label={`Filter by ${col.name}`}
          value={filters[col.name] ?? ""}
          onChange={(e) => setFilter(col.name, e.target.value || null)}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value="">{col.name} (all)</option>
          {col.sample_values.map((v) => (
            <option key={String(v)} value={String(v)}>{String(v)}</option>
          ))}
        </select>
      ))}
      <button onClick={clear} className="text-xs underline">Clear</button>
    </div>
  );
}
```

---

## 6. Testing Strategy

Full plan in `docs/test-strategy.md`. Headline numbers:

- **Backend (pytest):** ≥ 14 tests across upload, profiler, chart-picker, query engine, LLM tool layer.
- **Frontend (Vitest):** ≥ 7 tests across UploadDropzone, FilterBar, ChartGrid, ChatPanel, ExecutiveSummary.
- **E2E (Playwright):** the rubric's automated functional suite — full-flow upload → dashboard → filter → chat → summary, plus a "swap CSV" test that proves dataset-agnostic behavior.
- **TDD discipline:** every backend service is written test-first. Frontend components allow test-after for visual work but logic hooks (`useFilters`, `useDataset`) are test-first.
- **Edge-case fixtures:** a `tests/fixtures/` folder of tiny CSVs covering missing values, mixed types in one column, single-row file, all-null column, 100-column wide file, leading-zero IDs, Latin-1 encoding.

---

## 7. Boundaries

### Always do
- Run `uv run pytest` and `npm run test` locally **before every commit**.
- Validate every API boundary with a Pydantic model — no untyped `dict[str, Any]` returns.
- Validate uploaded CSV size **before parsing** (return 413 above 50 MB).
- Commit `.agent/skills/` as-is — never edit.
- Make atomic git commits with conventional-commit prefixes (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`).
- Record an ADR within 24 hours of any decision that constrains future work (provider, schema shape, library swap).

### Ask first
- Adding any new Python or npm dependency.
- Changing the database schema after Phase 2 ships.
- Modifying the public API shape (path, request body, response body).
- Switching LLM provider (this is what ADR-001 exists to prevent).
- Adding a new environment variable.
- Spending more than one task on a single bug — escalate to Zaman before going deeper.

### Never do
- Commit API keys, `.env`, or any secret.
- Hardcode column names from the credit-card dataset into application logic.
- Skip a failing test to "fix later" — either fix it or delete it with explicit approval.
- Edit files inside `.agent/skills/` (graded as-is).
- Deploy to production (out of scope).
- Send the full uploaded CSV body to the LLM — only profiles, queries, and aggregates.
- Use a non-parametrized SQL string anywhere — the query engine **builds** SQL, never accepts free-form SQL from the LLM.

---

## 8. Success Criteria (rubric-aligned)

| # | Criterion | Verifiable by |
|---|---|---|
| 1 | CSV upload accepts files up to 50 MB | `pytest test_upload.py::test_size_limit` |
| 2 | Uploads >50 MB return HTTP 413 with a clear message | same |
| 3 | Profiling completes within 5 s for files under 10 MB | `pytest test_profile.py::test_profile_perf` |
| 4 | Dashboard renders ≥ 4 and ≤ 6 visualizations automatically | Playwright `full-flow.spec.ts` |
| 5 | Filters update **every** visualization within 500 ms | Playwright timing assertion |
| 6 | Chat answers a sample question within 10 s and cites its source | Playwright + manual demo |
| 7 | Executive summary generates within 30 s of upload completion | Playwright |
| 8 | Executive summary contains ≥ 3 numeric facts from the data | Playwright regex check |
| 9 | Uploading a different CSV cleanly replaces the prior dataset | Playwright `swap-csv.spec.ts` |
| 10 | Data persists across a frontend page refresh | Playwright |
| 11 | All API responses validated by a Pydantic model | code review + schemathesis run |
| 12 | `pytest` ≥ 14 tests, all green | CI script in README |
| 13 | `vitest` ≥ 7 tests, all green | CI script in README |
| 14 | Single-command startup (`npm run dev:all`) on a clean machine | dry-run on classmate machine |

---

## 9. Out of Scope

- Authentication, multi-user accounts, RBAC.
- Production deployment, Docker, CI/CD pipelines beyond a local script.
- Mobile-responsive layout (desktop only).
- Custom ML models, supervised fraud detector, embeddings.
- Real-time collaborative editing.
- File formats other than CSV (no Excel, no Parquet, no JSON in MVP).
- Files larger than 50 MB at the upload boundary.
- LLM agents that mutate data — read-only tool surface only.
- LLM streaming UX — answers arrive as a single block.

---

## 10. Open Questions

| # | Question | Resolution |
|---|---|---|
| 1 | Which charting library? | **Recharts** — ADR-002. |
| 2 | Which LLM provider? | **Google Gemini 1.5 Flash** — ADR-001. |
| 3 | How do we store arbitrary CSVs in SQLite? | Per-dataset dynamic tables — ADR-003. |
| 4 | Should the executive summary be regenerable / editable? | Regenerable with a button; not editable in MVP. |
| 5 | How to handle very wide CSVs (100+ columns)? | Profile all; render at most 6 charts; surface the rest in an expandable column-list panel. *(Deferred to post-MVP.)* |
| 6 | Should the chat panel keep history across page reloads? | Yes — persisted in SQLite, scoped to dataset_id. |
| 7 | Latin-1 / Windows-1252 encoding fallback? | Out of MVP; documented as a known limitation. |

All decisions above are recorded in ADRs 001–003 or in this table; nothing remains open before implementation begins.
