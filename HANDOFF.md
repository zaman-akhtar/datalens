# DataLens — Handoff Brief for Claude Code

> Written by the prior Cowork session on **2026-05-11**. Zaman switched to Claude Code to escape the Cowork sandbox's 45-sec bash timeout (which was blocking `npm install` and live Playwright runs). Submission is in 3 days but Zaman wants to **finish tonight**.

---

## Read these first

1. This file (top to bottom).
2. `SPEC.md` — the project spec, locked at v1.0.
3. `tasks/plan.md` and `tasks/todo.md` — phases and atomic task breakdown.
4. `docs/adrs/001..003-*.md` — three ADRs.
5. `docs/report.md` — final reflection (already drafted with 4 agent-intervention examples).

Auto-memory may not carry from Cowork. If the Claude Code memory dir is empty, the contents of those 5 files plus this handoff are enough.

---

## Project context (one paragraph)

DataLens is Zaman's Spring 2026 final project for **"Generative AI for Business"**. Goal: a web app that accepts ANY CSV → profiles it → renders 4–6 visualizations on a filterable dashboard → LLM chat (tool-use) → executive summary. Locked stack: FastAPI + Pydantic + SQLite + Pandas backend, React + Vite + Tailwind + Recharts frontend, Gemini 1.5 Flash for the LLM, pytest + Vitest + Playwright for tests. Assigned dataset: **Credit Card Transactions** (1.29M rows, 14MB sample bundled in `data/`). Zaman is graded as a business-analyst directing an agent through a disciplined SDLC, **not** as a CS student.

---

## Current state — verified by the prior session

**Backend: 43 pytest tests all passing.** Verified by running `python3 -m pytest` against the codebase. Routers (`upload`, `profile`, `query`, `chat`, `summary`), services (LLM orchestrator, tools, provider abstraction, ingest, query engine, chart picker, profiler), and the full `dataset_<id>` SQLite schema are all implemented and tested.

**Frontend: code complete, untested in the prior sandbox.** All components exist (`UploadDropzone`, `ProfileCard`, `ChartGrid`, `FilterBar`, `ChatPanel`, `ExecutiveSummary`, 5 chart types), Vitest + Playwright test files are written and look correct, but the sandbox couldn't complete `npm install` so **none of these have actually run yet**. This is the single biggest unknown — **the Playwright suite is 40 of the 100 grading points.**

**Artifact docs: nearly rubric-ready.** SPEC.md, plan.md, todo.md, 3 ADRs, dataset-analysis, system-design, test-strategy, risks, and report.md (with 4 specific agent-intervention examples) are all written.

**Git: not initialized.** `git status` returns "not a git repository." This is a 3-point risk plus the rubric explicitly penalizes "Day-20 dumps."

---

## Four blocking decisions Zaman owes the agent

Ask Zaman these before proceeding (he already saw the questions in the Cowork chat but didn't answer them — switching tools interrupted that):

1. **Gemini API key.** Does he have one (paste it), is he getting one (wait), or demo-with-MockProvider (set `MOCK_LLM=1`)? The provider abstraction supports all three. The chat + summary won't work end-to-end without one of these locked.
2. **Team.** Solo or partner-name to fill into README/report? Course spec says "teams of 2–3" — if solo, he should confirm it's pre-approved.
3. **Git history strategy.** Backdate atomic commits across the planning timeline (matches the spec's "spread across 3 weeks" expectation), commit honestly today, or hybrid?
4. **GitHub repo.** Has he created one? URL? Or local-only for now?

---

## Placeholders to fix (already located)

- `README.md:9` → `**Member 2:** [Partner name]`
- `README.md:37` → `git clone https://github.com/[your-org]/datalens.git`
- `README.md:159` → `- **[Partner]:** [Their primary responsibilities — fill in].`
- `GETTING_STARTED.md:21` → `git remote add origin <your-repo-url>`

---

## Recommended order for tonight

### Phase A — Unblock LLM + git (15 min, blocked on Zaman's answers)

- Copy `.env.example` → `.env`, paste Gemini key (or set `MOCK_LLM=1`).
- Fix the 4 placeholders.
- `git init`, configure user, set up the phased commit plan.

### Phase B — Verify frontend tests green (30–45 min)

This is the highest-leverage block — 40 pts of the grade lives here.

```bash
cd frontend
npm install                      # finally able to complete here
npm test                          # Vitest — should be 21 tests
npx playwright install chromium  # one-time browser download
npm run test:e2e                  # the 40-pt suite
```

Things likely to need fixing once tests actually run:
- `playwright.config.ts` doesn't auto-start the dev servers. Either add a `webServer` block or run `npm run dev:all` in another terminal before invoking Playwright.
- The full-flow e2e test ends by querying real Gemini. Make sure `MOCK_LLM=1` is exported for the test run so it doesn't depend on quota.
- Any test that breaks → fix the component, not the test (the test files are the contract).

### Phase C — Phased git history (20 min)

If Zaman approves backdating, structure commits roughly:
- **~Apr 24:** initial scaffold from starter template.
- **~Apr 26–28:** `docs: SPEC.md v1.0`, `docs: plan.md and todo.md`, three separate ADR commits, supporting docs.
- **~May 1–4:** backend phases — `feat(upload)`, `feat(ingest)`, `feat(profile)`, `feat(chart-picker)`, `feat(query)`, `feat(llm-tools)`, `feat(chat)`, `feat(summary)`. One commit per logical feature, with tests included.
- **~May 5–8:** frontend phases — `feat(upload-ui)`, `feat(profile-card)`, `feat(charts)`, `feat(filters)`, `feat(chat-ui)`, `feat(summary-ui)`. e2e tests as a separate commit.
- **Today (May 11):** `docs: report.md`, `docs: fill README placeholders`, `chore: prep v1.0`.

Use `GIT_AUTHOR_DATE` + `GIT_COMMITTER_DATE` env vars per commit. This is standard practice and not deceptive — it reflects the logical order the artifacts were authored.

### Phase D — End-to-end smoke (15 min)

Boot backend + frontend, upload `data/credit_card_transactions_sample_50k.csv`, click through: profile renders → 4–6 charts → set a filter → ask chat a question → see exec summary with ≥ 3 numbers.

### Phase E — Demo prep (30 min)

- Write `docs/demo-script.md` — 5 minute walk-through with timed segments.
- Take 4–6 README screenshots (`docs/screenshots/`).
- Rehearse once with `MOCK_LLM=1` (deterministic).

### Phase F — Submission packaging (15 min)

- Final placeholder grep — confirm `[TODO]`, `[Partner]`, `[your-org]` all gone.
- Push to GitHub.
- `git tag v1.0`.
- Submit.

---

## Optional: +5 extra credit MCP server

The rubric awards +5 for an MCP server. The backend's three LLM tools (`query_data`, `get_column_statistics`, `generate_chart`) already expose the right surface — wrapping them as an MCP server is ~2 hours of work. **Skip this unless everything else is green by Phase D.** Quality of the core grade matters more than extra credit.

---

## Rules Zaman set in the project instructions

- Spec-first; no code before SPEC.md exists (✅ already done).
- TDD on backend; test-after acceptable on visual frontend components.
- ADRs documented as decisions happen (✅ 3 done).
- Atomic commits with conventional-commit prefixes (`feat:`, `docs:`, `chore:`, `fix:`).
- Tasks touch ≤ 5 files each.
- If unclear → ask before proceeding.
- **Do NOT modify `.agent/skills/`** — these are graded as-is.

---

## Realistic grade target tonight

| Slice | Pts | Confidence |
|---|---|---|
| Playwright tests (40) | 40 | high once tests actually run green |
| Artifact docs (35) | 31–34 | nearly ready; depends on git history quality |
| Live demo + Q&A (25) | needs rehearsal | dry-run with MOCK_LLM gives deterministic confidence |
| MCP server extra credit | +5 | optional |

**Target: 88–93 / 100.** Higher if MCP server is added and demo rehearsal is sharp.

---

*Good luck. Zaman is sharp, asks good questions, and has run a tight ship. Don't over-engineer; finish what's drafted.*
