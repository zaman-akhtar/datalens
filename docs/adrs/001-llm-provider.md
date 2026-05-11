# ADR-001: LLM Provider — Google Gemini 1.5 Flash

- **Status:** Accepted
- **Date:** 2026-05-04
- **Deciders:** Zaman + project partner
- **Supersedes:** —

---

## Context

DataLens needs an LLM that supports **function calling** so the chat panel can ground its answers in three Python tools (`query_data`, `get_column_statistics`, `generate_chart`). The course rubric allows any of: Google Gemini, Anthropic Claude, OpenAI GPT, Groq Llama. The decision is constrained by:

1. **Demo reliability.** A 30-minute live demo cannot be the moment we discover we are out of credits or rate-limited.
2. **Three-week budget.** No team funding for paid API credits; out-of-pocket costs need to stay near zero.
3. **Tool-use maturity.** The LLM must reliably emit structured tool calls and chain 2–4 of them per turn without going off the rails.
4. **Single swap point.** Whatever we pick, the choice must be reversible — `services/llm/provider.py` is the only file that should know which provider we use.

## Options considered

| Option | Free tier | Tool calling | Latency | Notes |
|---|---|---|---|---|
| **Google Gemini 1.5 Flash** | Yes — 15 RPM, 1 M tokens/day, free | Yes (mature) | ~1–2 s p50 | Clean SDK; explicit function declarations |
| Anthropic Claude (Haiku/Sonnet) | No — paid only | Yes (excellent) | ~1–3 s p50 | Strongest tool use, but credits required |
| OpenAI GPT-4o-mini | Limited free trial | Yes (mature) | ~1–2 s p50 | Predictable cost, but trial may expire mid-project |
| Groq (Llama 3.1) | Yes — generous | Yes (variable) | ~0.3–0.7 s p50 | Fastest, but tool-call reliability is hit-or-miss for chained calls |

## Decision

**Google Gemini 1.5 Flash** via the `google-generativeai` SDK.

- Free tier covers our development burn-rate (≤ 15 RPM is enough for two pair-programmers) and the live demo (≤ 50 requests in 30 minutes).
- Tool calling is first-class and well-documented.
- The SDK supports the OpenAI-style messages format closely enough that swapping to GPT-4o-mini later is a one-file change in `provider.py`.
- The course is GenAI-for-business, and Google AI Studio is the friendliest UX for inspecting prompts during the demo.

## Trade-offs

- **Lower benchmark scores than Claude Sonnet.** Mitigated: our prompts are short, the tool surface is small (3 functions), and the questions are tabular — Flash handles this well.
- **Free tier rate limits.** Mitigated: backoff with retry in `provider.py` plus a "rate-limited, try again" UI message; we will not call the LLM for chart rendering or filter changes (only for chat and summary).
- **Vendor lock-in risk.** Mitigated: provider wrapper exposes a generic `generate(messages, tools)` interface; switching costs ~30 minutes.

## Consequences

- Add `google-generativeai` to `pyproject.toml`.
- Add `GEMINI_API_KEY` to `.env.example` with a comment linking to the AI Studio page.
- Add a backup `OPENAI_API_KEY` line, **commented out**, in `.env.example` as escape hatch.
- The README must say "you need a free Gemini API key" in the setup section.
- Tests must never hit the real API — use `respx` to fake HTTP responses.

## Revisit conditions

- If quota becomes a recurring blocker before Day 14 → switch to OpenAI GPT-4o-mini and amend this ADR with status `Superseded`.
- If tool calling produces malformed structures > 5 % of the time → revisit.
