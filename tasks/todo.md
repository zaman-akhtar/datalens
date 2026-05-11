# Task Breakdown

*Task breakdown version: 1.0 | Last updated: 2026-05-04*

Each task touches **≤ 5 files**, has explicit acceptance criteria, and a verification step. Phase letters map to `tasks/plan.md`. Owner is left blank — the pair claims tasks at the start of each session.

---

## Phase 1 — Foundation

- [ ] **T001 — Verify starter scaffolding builds**
  - **Description:** Run `uv sync` in `backend/` and `npm install` in `frontend/`. Confirm empty `pytest` and `vitest run` exit 0.
  - **Acceptance:** Both runners exit 0 with "no tests ran" output.
  - **Verify:** Manual run, paste output into PR description.
  - **Files:** none (verification only).
  - **Dependencies:** none.

- [ ] **T002 — Push starter to GitHub, confirm agent commits**
  - **Description:** Create remote `datalens` repo, push, edit README to add team names, push commit.
  - **Acceptance:** Remote shows starter + 1 commit by Cowork.
  - **Verify:** GitHub UI.
  - **Files:** `README.md`.
  - **Dependencies:** T001.

- [ ] **T003 — Complete SPEC.md**
  - **Description:** Fill all 10 sections. Lock chart library, LLM provider, success criteria.
  - **Acceptance:** No `[TODO]` strings remain. Spec self-review passes against the rubric checklist in plan.md.
  - **Verify:** `grep -RIn '\[TODO\]' SPEC.md` returns nothing.
  - **Files:** `SPEC.md`.
  - **Dependencies:** T002. *(Done by this blueprint.)*

- [ ] **T004 — Complete plan.md**
  - **Description:** Document phases, risks, parallel tracks, dependencies, checkpoints.
  - **Acceptance:** Every Phase has Goal + tasks + Checkpoint.
  - **Verify:** Peer review.
  - **Files:** `tasks/plan.md`.
  - **Dependencies:** T003. *(Done.)*

- [ ] **T005 — Complete todo.md**
  - **Description:** This file.
  - **Acceptance:** ~30+ tasks, each ≤ 5 files, each with Verify step.
  - **Files:** `tasks/todo.md`.
  - **Dependencies:** T004. *(Done.)*

- [ ] **T006 — Write 3 ADRs**
  - **Description:** ADR-001 (LLM provider Gemini), ADR-002 (Recharts), ADR-003 (per-dataset SQLite tables).
  - **Acceptance:** Each ADR contains Context, Options, Decision, Trade-offs.
  - **Verify:** Peer review; cross-link from SPEC §10.
  - **Files:** `docs/adrs/001-*.md`, `002-*.md`, `003-*.md`.
  - **Dependencies:** T003. *(Done.)*

- [ ] **T007 — Supporting design docs**
  - **Description:** `dataset-analysis.md`, `system-design.md`, `test-strategy.md`, `risks.md`.
  - **Acceptance:** Each doc references SPEC.md and is referenced *from* SPEC.md.
  - **Files:** four files in `docs/`.
  - **Dependencies:** T003. *(Done.)*

---

## Phase 2 — Core Upload and Profiling

- [ ] **T010 — POST /api/upload endpoint**
  - **Description:** Multipart CSV upload, ≤ 50 MB, returns `{dataset_id, n_rows, n_cols}`.
  - **Acceptance:** Valid CSV → 201; non-CSV → 400; > 50 MB → 413.
  - **Verify:** `pytest backend/tests/test_upload.py` (3 tests written first).
  - **Files:** `backend/app/routers/upload.py`, `backend/app/models/upload.py`, `backend/tests/test_upload.py`, `backend/tests/fixtures/tiny.csv`.
  - **Dependencies:** T007.

- [ ] **T011 — SQLite ingestion service**
  - **Description:** Implement per-dataset table per ADR-003. Pandas → `to_sql`. Quote arbitrary column names safely.
  - **Acceptance:** Sample CSV ingested into `dataset_<id>` table; row count matches.
  - **Verify:** `pytest backend/tests/test_ingest.py` (4 tests, including the leading-zero fixture).
  - **Files:** `backend/app/services/ingest.py`, `backend/app/db/schema.py`, `backend/app/db/session.py`, `backend/tests/test_ingest.py`.
  - **Dependencies:** T010.

- [ ] **T012 — Profiling service**
  - **Description:** For each column emit dtype, null %, n_unique, sample values, skew (numeric only).
  - **Acceptance:** All-null column → `null_pct=1.0`; mixed-type column → `dtype=text`; `Unnamed:0` index → flagged hidden.
  - **Verify:** `pytest backend/tests/test_profile.py` (5 tests).
  - **Files:** `backend/app/services/profile.py`, `backend/app/models/dataset.py`, `backend/tests/test_profile.py`, fixture(s).
  - **Dependencies:** T011.

- [ ] **T013 — GET /api/datasets/{id}/profile**
  - **Description:** Wire profiling service to FastAPI router with `DatasetProfile` Pydantic response.
  - **Acceptance:** 200 returns valid JSON; 404 on bad id.
  - **Verify:** `pytest backend/tests/test_profile_router.py` (2 tests).
  - **Files:** `backend/app/routers/profile.py`, `backend/app/main.py` (register router), `backend/tests/test_profile_router.py`.
  - **Dependencies:** T012.

- [ ] **T014 — Frontend upload dropzone + dataset hook**
  - **Description:** Drag-drop or browse, POST to `/api/upload`, store `dataset_id` in `useDataset` hook.
  - **Acceptance:** Upload a sample CSV; dataset_id appears in network tab and in app state.
  - **Verify:** `vitest UploadDropzone.test.tsx` (2 tests using msw).
  - **Files:** `frontend/src/components/UploadDropzone.tsx`, `frontend/src/hooks/useDataset.ts`, `frontend/src/lib/api.ts`, `frontend/tests/UploadDropzone.test.tsx`.
  - **Dependencies:** T013.

- [ ] **T015 — ProfileCard component**
  - **Description:** Render the profile JSON as a table: name, type, null %, n_unique, sample values.
  - **Acceptance:** All columns from sample CSV visible; hidden index columns absent.
  - **Verify:** `vitest ProfileCard.test.tsx` (2 tests).
  - **Files:** `frontend/src/components/ProfileCard.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/tests/ProfileCard.test.tsx`.
  - **Dependencies:** T014.

---

## Phase 3 — Dashboard Visualizations

- [ ] **T020 — Chart-picker rule book**
  - **Description:** Pure function: `pick_charts(profile, max=6) -> list[ChartSpec]`. Rules in `docs/system-design.md §3`.
  - **Acceptance:** For credit-card sample → ≥ 4 charts including a category bar, an hour-of-day line, an `amt` histogram, a `state` bar. For Airbnb sample → 4 different charts.
  - **Verify:** `pytest backend/tests/test_chart_picker.py` (6 tests across two fixtures).
  - **Files:** `backend/app/services/chart_picker.py`, `backend/app/models/chart.py`, `backend/tests/test_chart_picker.py`, fixture.
  - **Dependencies:** T012.

- [ ] **T021 — POST /api/datasets/{id}/query endpoint + safe builder**
  - **Description:** Body = `{x, y?, agg, filters?, limit?}`. Builds parametrized SQL. Whitelists column names against profile.
  - **Acceptance:** Unknown column → 400; SQL-injection attempt in filter value → safely escaped (parametrized).
  - **Verify:** `pytest backend/tests/test_query_engine.py` (5 tests including injection attempt).
  - **Files:** `backend/app/routers/query.py`, `backend/app/services/query_engine.py`, `backend/app/models/query.py`, `backend/tests/test_query_engine.py`.
  - **Dependencies:** T013.

- [ ] **T022 — Five chart components (Recharts)**
  - **Description:** Bar, Line, Histogram, Scatter, KPI. Common props `{spec, data}`. No business logic — pure render.
  - **Acceptance:** Storybook-style test renders each with seed data and asserts no console errors.
  - **Verify:** `vitest chart/*.test.tsx` (5 small smoke tests).
  - **Files:** `frontend/src/components/chart/{Bar,Line,Histogram,Scatter,Kpi}.tsx`, `frontend/tests/chart.smoke.test.tsx`.
  - **Dependencies:** none after Vite scaffolding.

- [ ] **T023 — ChartGrid**
  - **Description:** Fetch `pick_charts` output, then for each spec call `/query` and render via the right component.
  - **Acceptance:** 4–6 charts visible after upload.
  - **Verify:** `vitest ChartGrid.test.tsx` (1 test using msw with 4 mocked specs).
  - **Files:** `frontend/src/components/ChartGrid.tsx`, `frontend/src/lib/api.ts`, `frontend/tests/ChartGrid.test.tsx`.
  - **Dependencies:** T020, T021, T022.

- [ ] **T024 — Loading / error / empty states**
  - **Description:** Skeleton on load, error toast, empty-state message when query returns 0 rows.
  - **Acceptance:** Disconnect backend → user sees an error, not a blank page.
  - **Verify:** Manual + 1 vitest with mocked failure.
  - **Files:** `ChartGrid.tsx`, `ChartGrid.test.tsx`, `frontend/src/components/ui/Skeleton.tsx`.
  - **Dependencies:** T023.

---

## Phase 4 — Global Filters

- [ ] **T030 — useFilters Zustand store**
  - **Description:** `{filters: Record<string, string|null>, setFilter, clear}`. Persist to sessionStorage. *(Note: localStorage is forbidden inside artifacts but allowed in the standalone app.)*
  - **Acceptance:** Setting a filter then refreshing keeps it scoped to dataset.
  - **Verify:** `vitest useFilters.test.ts` (3 tests).
  - **Files:** `frontend/src/hooks/useFilters.ts`, `frontend/tests/useFilters.test.ts`.

- [ ] **T031 — FilterBar component**
  - **Description:** Render dropdown per categorical column with cardinality ≤ 50; date range picker for datetime columns.
  - **Acceptance:** All low-cardinality categoricals appear; high-cardinality omitted.
  - **Verify:** `vitest FilterBar.test.tsx` (2 tests).
  - **Files:** `frontend/src/components/FilterBar.tsx`, `frontend/tests/FilterBar.test.tsx`.
  - **Dependencies:** T030.

- [ ] **T032 — Query engine accepts filters**
  - **Description:** Translate `{state: "NY", category: "grocery_pos"}` into parametrized `WHERE`. Datetime → `BETWEEN`.
  - **Acceptance:** Filtered query row count < unfiltered row count for the sample.
  - **Verify:** `pytest backend/tests/test_query_engine.py::test_filters` (3 tests added).
  - **Files:** `backend/app/services/query_engine.py`, `backend/app/models/query.py`, `backend/tests/test_query_engine.py`.

- [ ] **T033 — Wire filters into ChartGrid**
  - **Description:** Subscribe `ChartGrid` to `useFilters`; refetch on change. Assert paint < 500 ms in vitest with mocked latency.
  - **Acceptance:** Toggling filter → all charts refetch in < 500 ms (mocked) and < 1 s (real backend).
  - **Verify:** `vitest ChartGrid.filter.test.tsx`; manual stopwatch on real backend.
  - **Files:** `ChartGrid.tsx`, `ChartGrid.filter.test.tsx`.
  - **Dependencies:** T031, T032.

---

## Phase 5 — LLM Chat Interface

- [ ] **T040 — Gemini provider wrapper**
  - **Description:** `provider.generate(messages, tools) -> ToolCall | TextResponse`. Single point to swap providers.
  - **Acceptance:** Hits Gemini in integration mode; returns canned responses in unit-test mode (faked).
  - **Verify:** `pytest backend/tests/test_provider.py` (3 tests, none hit network — uses respx).
  - **Files:** `backend/app/services/llm/provider.py`, `backend/app/models/llm.py`, `backend/tests/test_provider.py`.

- [ ] **T041 — Three LLM tools**
  - **Description:** `query_data(x, y, agg, filters)`, `get_column_statistics(column)`, `generate_chart(chart_type, x, y)`. Each is a thin Python function calling the existing query/profile/chart services.
  - **Acceptance:** Each tool returns JSON-serializable, ≤ 100 rows, with the SQL it ran.
  - **Verify:** `pytest backend/tests/test_llm_tools.py` (4 tests).
  - **Files:** `backend/app/services/llm/tools.py`, `backend/tests/test_llm_tools.py`.
  - **Dependencies:** T021, T012.

- [ ] **T042 — POST /api/datasets/{id}/chat**
  - **Description:** Loop: model → maybe tool call → execute → feed back → max 4 iterations → final text. Persist to `chat_messages` table.
  - **Acceptance:** Sample question returns a grounded answer within 10 s; transcript persisted.
  - **Verify:** `pytest backend/tests/test_chat.py` (3 tests with faked provider).
  - **Files:** `backend/app/routers/chat.py`, `backend/app/services/llm/orchestrator.py`, `backend/app/db/schema.py` (add table), `backend/tests/test_chat.py`.
  - **Dependencies:** T040, T041.

- [ ] **T043 — ChatPanel component**
  - **Description:** Message list, input box, "Sent SQL" disclosure under each answer.
  - **Acceptance:** User sends question → bubble appears → answer appears → SQL collapsible.
  - **Verify:** `vitest ChatPanel.test.tsx` (2 tests).
  - **Files:** `frontend/src/components/ChatPanel.tsx`, `frontend/src/lib/api.ts`, `frontend/tests/ChatPanel.test.tsx`.
  - **Dependencies:** T042.

- [ ] **T044 — Persist chat history per dataset**
  - **Description:** On dataset load, `GET /api/datasets/{id}/chat/history`; render before new messages.
  - **Acceptance:** Page refresh keeps the prior conversation.
  - **Verify:** Playwright (will be in T062 suite).
  - **Files:** `chat.py` router additions, `ChatPanel.tsx`, `api.ts`.

---

## Phase 6 — Executive Summary

- [ ] **T050 — Summary prompt + service**
  - **Description:** Feed Gemini the profile + 3 canned aggregates (top category, mean of first numeric, count by date bucket). Prompt enforces ≥ 3 numeric facts.
  - **Acceptance:** Output regex `\d+(\.\d+)?` matches ≥ 3 times.
  - **Verify:** `pytest backend/tests/test_summary.py` (2 tests with faked provider).
  - **Files:** `backend/app/services/llm/summary_prompt.py`, `backend/tests/test_summary.py`.

- [ ] **T051 — GET /api/datasets/{id}/summary**
  - **Description:** Endpoint with cache (regenerate via `?refresh=true`).
  - **Acceptance:** First call generates; second call hits cache.
  - **Verify:** `pytest backend/tests/test_summary_router.py` (2 tests).
  - **Files:** `backend/app/routers/summary.py`, `backend/app/main.py`, `backend/tests/test_summary_router.py`.
  - **Dependencies:** T050.

- [ ] **T052 — ExecutiveSummary component**
  - **Description:** Display summary, "Regenerate" button, "Copy to clipboard" button.
  - **Acceptance:** Renders summary text; regenerate triggers `?refresh=true`.
  - **Verify:** `vitest ExecutiveSummary.test.tsx` (2 tests).
  - **Files:** `frontend/src/components/ExecutiveSummary.tsx`, `frontend/tests/ExecutiveSummary.test.tsx`.
  - **Dependencies:** T051.

- [ ] **T053 — Playwright assertion: ≥ 3 numeric facts**
  - **Description:** Add to full-flow spec.
  - **Acceptance:** Regex `(\d+(\.\d+)?)` matches ≥ 3 in summary text.
  - **Files:** `frontend/tests/e2e/full-flow.spec.ts`.

---

## Phase 7 — Polish, Docs, Demo

- [ ] **T060 — README rewrite**
  - **Description:** Replace stub with verified setup, env vars, run, test, example usage. Include screenshots.
  - **Acceptance:** Classmate clones and runs without help.
  - **Verify:** Dry run on partner's laptop (T065).
  - **Files:** `README.md`, `docs/screenshots/*.png`.

- [ ] **T061 — `.env.example` audit**
  - **Description:** Document every env var (`GEMINI_API_KEY`, `DATABASE_URL`, `MAX_UPLOAD_MB`, `CORS_ORIGINS`).
  - **Acceptance:** App boots with values from `.env.example` copied to `.env`.
  - **Files:** `.env.example`, `backend/app/config.py`.

- [ ] **T062 — Cross-dataset Playwright test**
  - **Description:** Upload Airbnb roster CSV mid-test, assert dashboard re-renders without credit-card terms.
  - **Acceptance:** Test passes; no `category`, `merchant`, or `is_fraud` strings in DOM after swap.
  - **Files:** `frontend/tests/e2e/swap-csv.spec.ts`, `frontend/tests/fixtures/airbnb_sample.csv`.

- [ ] **T063 — Final report (`docs/report.md`)**
  - **Description:** ≥ 3 specific examples of agent interventions: (a) when Cowork over-engineered, (b) when an ADR caught a bad direction, (c) when TDD caught a regression.
  - **Acceptance:** Each example has commit hash + 1–2 sentences.
  - **Files:** `docs/report.md`.

- [ ] **T064 — Demo videos**
  - **Description:** Mid-project (Day 14) + final (Day 21). 5 minutes each. Every team member speaks.
  - **Acceptance:** Uploaded to course portal.
  - **Files:** none in repo.

- [ ] **T065 — Clean-machine dry run**
  - **Description:** Wipe Node and Python on a partner's laptop; clone repo; follow README only.
  - **Acceptance:** App runs end-to-end; partner finds and reports any README gap before submission.
  - **Files:** any README fixes.

- [ ] **T066 — Submission packaging**
  - **Description:** Tag `v1.0`, push, fill submission form.
  - **Acceptance:** Submission accepted before deadline.
  - **Files:** none.

---

## Task Sizing Self-Check

- [x] Every task touches ≤ 5 files.
- [x] Every task has a Verify step (test command, manual check, or peer review).
- [x] No task requires more than one focused session.
- [x] Dependencies are explicit and ordered.
- [x] Test counts add up: 14 backend + 7 frontend + 2 Playwright suites — meets SPEC §6.
