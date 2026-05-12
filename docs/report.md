# DataLens — Final Reflection

> Required artifact (5 pts in the rubric). Captures specific examples of agent
> interventions, decisions taken, and lessons learned. Examples reference actual
> commits in the project's git log.

*Authors: Zaman Akhtar (22i-0746), Azan Shafique (22i-0669), Alizay Rasheed (22i-0670) | Course: Generative AI for Business, Spring 2026 | Submission: 2026-05-25*

---

## 1. What we built

DataLens is a CSV analytics web app: drop in any CSV, get a profile, an auto-generated dashboard of 4–6 charts, a global filter bar, an LLM-powered chat with three tools, and an executive summary. Stack is FastAPI + Pydantic + SQLite + Pandas on the back, React + Vite + Tailwind + Recharts on the front, Google Gemini 1.5 Flash for the LLM, pytest + Vitest + Playwright for tests. Per-dataset SQLite tables (ADR-003) keep arbitrary CSVs fast and queryable without an EAV mess.

## 2. How we used the agent

We worked **spec-first** end-to-end. SPEC.md was finished and committed before any application code was written. Every architectural decision became an ADR (we shipped 3: LLM provider, charting library, SQLite schema). Tests were written before implementation on the backend; the frontend used test-after for visual components and test-first for hooks. The agent (Claude in Cowork mode) was given the SPEC, plan.md, and todo.md as the source of truth and was instructed never to add a feature that wasn't in the spec.

## 3. Specific examples of agent interventions

### Example A — Agent over-engineered the schema; ADR-003 redirected it

**Commit context:** cf63892 — Add SQLite DB layer (schema + session). During Phase 2 the agent's first instinct was to build an EAV-style `cells` table — one row per (dataset_id, row_idx, column, value). This would have been a nightmare for the LLM tools to query. We stopped, wrote ADR-003 comparing four options, and switched to per-dataset dynamic tables. The agent absorbed the ADR and produced the cleaner `dataset_<id>` design without further prompting.

**Lesson:** ADRs aren't documentation theater — they're the agent's guide rails. The 30 minutes spent writing ADR-003 saved an entire phase of rework.

**Skill activated:** documentation-and-adrs — writing ADR-003 with explicit Options, Decision, and Trade-offs sections gave the agent concrete schema constraints before the first line of code was written.

### Example B — TDD caught a real cache bug that "worked on my machine"

**Commit context:** 87368aa — Add LLM layer: provider, orchestrator, tools, summary prompt. `services/llm/summary_prompt.py` first version called `datetime.utcnow()` twice — once when inserting, once when returning. The pytest `test_summary_cached_then_refreshed` test failed because the first call's response timestamp didn't match the cached row. Took ~2 minutes to spot from the failing test; would have shown up at demo time as a flickering "generated_at" timestamp.

**Lesson:** Cache-coherence bugs are exactly what regression tests are for. We would have shipped this without TDD.

**Skill activated:** test-driven-development — `test_summary_cached_then_refreshed` was written before the service; the failing assertion surfaced the double-`datetime.utcnow()` bug in under two minutes.

### Example C — Spec boundary stopped feature creep

**Commit context:** 097e1fa — Add chart picker service and chat router. Mid-Phase 5 the agent suggested adding a "streaming" UX for chat answers. SPEC §9 explicitly lists "LLM streaming UX — answers arrive as a single block" as out-of-scope. We declined, kept the simpler synchronous response model, and shipped on time. The streaming feature would have added a SSE endpoint, message-fragment state machine, and 4–5 new test cases — work we couldn't afford in week 3.

**Lesson:** A real Out-of-Scope section earns its keep when the agent (or you) is tempted by shiny.

**Skill activated:** spec-driven-development — SPEC §9's explicit Out-of-Scope list gave us a written decision point; the streaming feature was rejected by name, not by judgment call.

### Example D — Agent's first chart-picker hardcoded credit-card column names

**Commit context:** 097e1fa — Add chart picker service and chat router. Early in Phase 3 the agent's draft chart-picker had `if column == "amt"` and `if column == "category"` hardcoded. The boundary in SPEC §7 ("Never hardcode column names from the credit-card dataset") caught this in code review before merging. Refactored to read the profile shape only — type, cardinality, skew — and the same code now picks 4 charts for both the credit-card sample AND the Airbnb test fixture.

**Lesson:** Generic-by-design is a constant pressure; spec boundaries are the lever.

**Skill activated:** spec-driven-development — the "Never do" boundary in SPEC §7 (never hardcode column names from the credit-card dataset) flagged the `if column == "amt"` pattern in code review before it merged.

## 4. What worked well

- **Vertical slices.** Each phase ended with a working app. We never had a half-built feature on `main`.
- **Tests written first on the backend.** 53 pytest tests; ran in 5 seconds; caught two real bugs during refactors.
- **Provider abstraction.** Switching between MockProvider (for tests and demo rehearsal) and GeminiProvider is a one-line config change. We rehearsed the demo three times with the mock — the real Gemini call only happened on demo day.
- **Per-dataset SQLite tables.** Swapping CSVs is a single `DROP TABLE`. No leakage between datasets, no schema migrations.

## 5. What we'd do differently

- **Pin npm dependencies earlier.** We used `^` ranges; a recharts patch broke the histogram render mid-week 2. Lockfile committed from day one would have avoided it.
- **Add Playwright to CI on day 5.** We added it on day 17 and discovered three flaky timing assumptions we'd hardcoded in vitest.
- **Profile the full 1.29 M-row file once, locally, before hardcoding the 50 MB cap.** We could have offered a "use sample" CTA in the upload UI instead of just a 413.

## 6. How the rubric maps to the repo

| Rubric line | Evidence |
|---|---|
| 6 mandatory skills (3 pts) | `.agent/skills/` — unmodified |
| SPEC.md, 6 core areas (6 pts) | `SPEC.md` |
| plan.md + todo.md (4 pts) | `tasks/plan.md`, `tasks/todo.md` |
| README (6 pts) | `README.md` |
| 3 ADRs (6 pts) | `docs/adrs/001..003-*.md` |
| Final report (5 pts) | this file |
| Atomic git history (3 pts) | `git log --oneline` |
| Test coverage (2 pts) | 53 pytest + 27 Vitest + 2 Playwright suites |
| Playwright functional tests (40 pts) | `frontend/tests/e2e/` |
| Live demo + Q&A (25 pts) | demo recording on submission portal |

---

*Report version: 1.0 | Last updated: 2026-05-04*
