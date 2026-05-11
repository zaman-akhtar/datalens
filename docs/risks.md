# Risk Analysis — DataLens

Top 5 things that can sink the project, ranked by **expected damage** (likelihood × impact). Each has a concrete mitigation tracked as a task in `todo.md`.

---

## R1 — Live-demo LLM failure

**Likelihood:** Medium · **Impact:** High · **Score:** 9 / 16

Gemini's free tier could rate-limit, throw a quota error, or return malformed tool calls during the 30-minute live demo. With 25 of 100 rubric points riding on the demo, this is the biggest single risk.

**Mitigations**
- The provider wrapper exposes a generic `generate(messages, tools)` interface; switching to OpenAI is a one-file change. `OPENAI_API_KEY` is pre-staged in `.env.example` (commented).
- A `MOCK_LLM=1` flag swaps `provider.py` for a deterministic fake. We rehearse the demo with both real and mocked providers.
- The chat panel surfaces "AI is rate-limited, try again in 30 s" instead of crashing. The dashboard, filters, profile, and (cached) summary keep working without the LLM.
- Demo-day discipline: hit the upload + chat path **once** during setup to warm caches. Have a screen recording fallback if everything melts.

---

## R2 — Dataset blows up the upload limit / SQLite

**Likelihood:** Medium · **Impact:** High · **Score:** 9 / 16

The full `credit_card_transactions.csv` is 338 MB / 1.29 M rows — far above the 50 MB SPEC limit. If anyone (teammate, grader, ourselves) tries to upload it, things break.

**Mitigations**
- Hard 50 MB cap at the upload boundary, returning 413 with a clear hint to use the sample.
- `data/credit_card_transactions_sample_50k.csv` (14 MB) ships in the repo as the canonical demo file.
- README's "Quickstart" tells the user to drag *this specific file* in.
- Playwright tests run against the sample, not the full file.
- A separate `scripts/make_sample.py` documents how to regenerate the sample if needed.

---

## R3 — Chart-picker produces ugly or empty charts on the demo CSV

**Likelihood:** Medium · **Impact:** Medium · **Score:** 6 / 16

The chart-picker is a rule book, not an ML model. On a wildly skewed or unusual dataset it can pick a chart that looks bad (e.g. a 500-bar bar chart, a histogram of an all-zeros column).

**Mitigations**
- Top-N cap (15) for categorical bars with an "Other" bucket.
- Skew threshold for log scaling; null-pct check before picking a column.
- Two known-good fallback datasets (the credit-card sample and an Airbnb subset) are part of the test fixture set and the demo run-book.
- Chart components have an empty-state ("Not enough data to plot") instead of crashing.

---

## R4 — Spec drift mid-build

**Likelihood:** Medium · **Impact:** Medium · **Score:** 6 / 16

Three weeks is enough time for "wouldn't it be cool if…" features to creep in. Each one risks a half-built feature on the main branch at submission time.

**Mitigations**
- The "Ask first" boundary in SPEC §7 covers any new dependency, schema change, or API shape change.
- Every feature change requires a SPEC.md edit + commit *before* the code commit. Reviewable in `git log`.
- Plan checkpoints (between every phase) include a "no orphan TODOs" grep.
- The `incremental-implementation` skill is graded; obeying it polices drift naturally.

---

## R5 — Teammate availability gap during Week 2 (LLM phase)

**Likelihood:** Low · **Impact:** High · **Score:** 4 / 16

Phase 5 (LLM chat) is the most cross-functional and the hardest to recover if a teammate goes dark mid-implementation.

**Mitigations**
- Pair-program Phase 5 from start to finish — single point of project failure.
- All Phase 1–4 work is sized to be solo-completable so the other phases stay parallelizable.
- The `git-workflow-and-versioning` skill (graded) enforces atomic commits, so any partial Phase 5 work is recoverable from `git log`.
- README's "Getting Started" is good enough that a third teammate, if added, can come up to speed in < 1 hour.

---

## Lower-tier risks (tracked but not in the top 5)

| Risk | Mitigation |
|---|---|
| Playwright flake on slow CI | Pin browser version; run E2E locally in pre-commit, not in CI |
| `cc_num` precision loss in JS | Profiler casts > 2^53 ints to string in ingest |
| CORS misconfiguration on demo machine | `.env.example` documents `CORS_ORIGINS=http://localhost:5173` |
| `.env` accidentally committed | `.gitignore` has `.env`; pre-commit hook with `git-secrets` |
| Submission deadline missed | T065 dry-run scheduled for Day 20, T066 packaging Day 21 morning |

---

*Risk analysis version: 1.0 | Last updated: 2026-05-04*
