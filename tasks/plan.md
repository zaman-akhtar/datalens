# Implementation Plan

*Plan version: 1.0 | Last updated: 2026-05-04 | Owner: Zaman + 1 partner*

---

## Plan Summary

We build DataLens in seven thin vertical slices over three weeks. Each slice ends with a working app and green tests — never a half-built feature on the main branch. Slice order is upload → profile → dashboard → filters → chat → executive summary → polish. The first two days are pure scaffolding and spec. The last two days are demo prep and a clean-machine dry run. Total: **~33 atomic tasks** in `todo.md`, each touching ≤ 5 files. We use **TDD on the backend** (test first, then implementation) and **test-after on visual frontend components** (logic hooks remain test-first). Every architectural decision is recorded in an ADR within 24 hours. Git commits are atomic with conventional-commit prefixes.

---

## Major Phases and Milestones

### Phase 1 — Foundation (Days 1–3)

**Goal:** spec, plan, and task list are solid; scaffolding builds; agent can commit; CI can run empty test suites.

- T001 Verify starter template builds (`uv sync`, `npm install`, empty `pytest`, empty `vitest`).
- T002 Push to GitHub; confirm Cowork can commit.
- T003 Complete SPEC.md (✅ done in this blueprint).
- T004 Complete plan.md (this file).
- T005 Complete todo.md.
- T006 Write ADRs 001 (LLM provider), 002 (charting library), 003 (SQLite schema strategy).
- T007 Write `docs/dataset-analysis.md`, `docs/system-design.md`, `docs/test-strategy.md`, `docs/risks.md`.

**Checkpoint:** Both test runners pass with zero tests. All planning artifacts merged to `main` in atomic commits. README has a working "Getting Started" stub.

### Phase 2 — Core Upload and Profiling (Days 4–7)

**Goal:** user uploads a CSV and sees a profile.

- T010 CSV upload endpoint with size cap and Pydantic validation.
- T011 SQLite ingestion — per-dataset dynamic table per ADR-003.
- T012 Type-inference and profiling service.
- T013 `GET /api/datasets/{id}/profile` endpoint.
- T014 Frontend upload dropzone + dataset hook.
- T015 ProfileCard component.

**Checkpoint:** upload `credit_card_transactions_sample_50k.csv`, see column names, types, null %, cardinality on screen. **First Playwright smoke test passes.**

### Phase 3 — Dashboard Visualizations (Days 7–10)

**Goal:** auto-generated dashboard with 4–6 charts.

- T020 Chart-picker rule book (profile → list of `(chart_type, x, y)`).
- T021 `POST /api/datasets/{id}/query` endpoint backed by the safe query builder.
- T022 Five chart components (Bar, Line, Histogram, Scatter, KPI).
- T023 ChartGrid component renders the 4–6 picks.
- T024 Loading/error/empty states.

**Checkpoint:** four meaningful charts render for the assigned dataset and for a wildly different roster CSV (e.g. NYC Airbnb).

### Phase 4 — Global Filters (Days 10–12)

**Goal:** changing one filter updates every chart.

- T030 `useFilters` Zustand store + tests.
- T031 FilterBar component.
- T032 Query layer accepts filter dict and translates to parametrized WHERE clauses.
- T033 Wire filters into ChartGrid; assert 500 ms budget in Vitest.

**Checkpoint:** filter `state = NY` → all charts update in < 500 ms.

### Phase 5 — LLM Chat Interface (Days 12–16)

**Goal:** plain-English question → tool-grounded answer.

- T040 LLM provider wrapper (Gemini) — single point to swap.
- T041 Three tools: `query_data`, `get_column_statistics`, `generate_chart`.
- T042 `POST /api/datasets/{id}/chat` endpoint with conversation persistence.
- T043 ChatPanel component + tool-call display ("ran SELECT … LIMIT 100 → 14 rows").
- T044 Chat-history persistence in SQLite.

**Checkpoint:** ask "which category has the highest fraud rate?" — answer + the SQL the LLM ran appears in < 10 s.

### Phase 6 — Executive Summary (Days 16–18)

**Goal:** one-paragraph summary with ≥ 3 numeric facts.

- T050 Summary prompt template (dataset-agnostic, fed only profile + 3 aggregate snapshots).
- T051 `GET /api/datasets/{id}/summary` endpoint with caching.
- T052 ExecutiveSummary component with regenerate button.
- T053 Playwright assertion: ≥ 3 numeric facts present.

**Checkpoint:** summary appears in < 30 s of upload.

### Phase 7 — Polish, Docs, Demo (Days 18–21)

**Goal:** demo-ready, classmate can clone-and-run.

- T060 README rewrite with verified setup steps.
- T061 `.env.example` audit + add any missing keys.
- T062 Cross-dataset Playwright test (swap CSV).
- T063 Final report (`docs/report.md`) with **specific examples of agent interventions**.
- T064 Mid-project / final demo video.
- T065 Clean-machine dry run on a partner's laptop.
- T066 Submission packaging.

**Checkpoint:** rubric self-audit (40 + 35 + 25 = 100, plus ≤ 10 extra credit) shows green on every line.

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Gemini quota exhaustion mid-demo** | Med | High | Pre-warm a backup OpenAI key in `.env.example` (commented); the provider wrapper is the single swap point. |
| **Full 1.29 M-row file blows up SQLite or memory on grader's laptop** | High | High | Default upload limit is 50 MB. The dev sample is 14 MB. The full file is documented as out-of-scope for upload; grader uses the sample. |
| **Chart-picker produces ugly/unreadable charts on the live demo dataset** | Med | Med | Keep a curated `roster_sample.csv` (Airbnb subset) as a known-good fallback; rehearse with both. |
| **Tool-call loop with the LLM never terminates** | Low | High | Hard cap at 4 tool calls per chat turn; surface "I ran out of tool calls" to the user. |
| **Teammate availability uneven Week 2** | Med | Med | Pair-program Phase 5 (LLM) — single point of project failure. Phase 3 (charts) and Phase 4 (filters) are parallelizable across two people. |
| **Spec drifts during build (we add features that aren't in SPEC.md)** | Med | Low | "Ask first" boundary; any change requires a SPEC.md edit + commit before code. |

---

## Parallel Work Opportunities

After T015 (ProfileCard) ships, the two teammates can split:

- **Track A (backend-leaning):** T020 chart-picker → T021 query endpoint → T032 filter translator → T040–T042 LLM layer.
- **Track B (frontend-leaning):** T022 chart components → T023 ChartGrid → T030–T031 filters UI → T043 ChatPanel.

Tracks converge at T033 (wire filters into ChartGrid) and again at T043 (chat UI calls chat endpoint). Phase 6 and Phase 7 are paired again.

---

## Dependency Notes

- The frontend upload component (T014) depends on the upload endpoint contract being defined in T010 — interface frozen as a Pydantic model in `backend/app/models/upload.py`.
- The chart-picker (T020) depends on the profile output format being frozen in T012 — contract is `DatasetProfile` in `models/dataset.py`.
- The LLM tool layer (T041) depends on the query engine (T021) and column-stats logic (folded into T012) — tools are thin wrappers, not separate logic.
- Filter translation (T032) depends on column profile types — categorical → equality, numeric → range, datetime → range.
- The executive summary prompt (T050) depends on profile + a small set of canned aggregates (`count by column[0]`, `mean amt`, `top-N category`) — runs the same query engine, no new code path.

---

## Verification Checkpoints (between every phase)

1. `uv run pytest` is green.
2. `npm run test` is green.
3. `npm run dev:all` boots the app without console errors.
4. `git log --oneline` shows atomic commits for the phase, not one giant blob.
5. No `TODO`, `FIXME`, or `XXX` strings have shipped (`ripgrep -i 'todo|fixme|xxx' backend/app frontend/src`).
6. The week's ADRs are written and merged.

If any of these fail → stop, fix, then move to the next phase.
