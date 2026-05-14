"""LLM provider abstraction.

Three implementations:
- GeminiProvider: real Google Gemini via `google-generativeai`.
- GroqProvider: Groq cloud inference via `groq` (OpenAI-compatible).
- MockProvider: deterministic, used when MOCK_LLM=1 or in tests.

The interface is the **single swap point** for changing provider (ADR-001).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from app.config import get_settings


@dataclass
class ToolCall:
    """One tool invocation requested by the model."""

    name: str
    args: dict[str, Any]


@dataclass
class ProviderResponse:
    """Either text (final answer) or one or more tool calls."""

    text: str | None = None
    tool_calls: list[ToolCall] | None = None

    @property
    def is_tool_call(self) -> bool:
        return bool(self.tool_calls)


class LLMProvider(Protocol):
    """Generic interface — every provider must satisfy this signature."""

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
    ) -> ProviderResponse: ...


# ---------------------------------------------------------------------------
# Gemini implementation
# ---------------------------------------------------------------------------


class GeminiProvider:
    """Wraps google-generativeai. Imports lazily so test runs without the SDK
    installed still succeed (MOCK_LLM=1 path)."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
    ) -> ProviderResponse:
        # Convert our generic message list to the Gemini format.
        history = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})

        gen_kwargs: dict[str, Any] = {}
        if tools:
            gen_kwargs["tools"] = [
                {
                    "function_declarations": [
                        {
                            "name": t["name"],
                            "description": t["description"],
                            "parameters": t["parameters"],
                        }
                        for t in tools
                    ]
                }
            ]
        if system:
            gen_kwargs["system_instruction"] = system

        model = self._genai.GenerativeModel(self._model_name, **gen_kwargs)
        try:
            resp = model.generate_content(history)
        except Exception as e:  # noqa: BLE001
            raise ProviderError(str(e)) from e

        # Parse tool calls
        try:
            cand = resp.candidates[0]
            for part in cand.content.parts:
                fn = getattr(part, "function_call", None)
                if fn and fn.name:
                    args = dict(fn.args) if fn.args else {}
                    return ProviderResponse(tool_calls=[ToolCall(name=fn.name, args=args)])
        except (AttributeError, IndexError):
            pass

        return ProviderResponse(text=getattr(resp, "text", "") or "")


# ---------------------------------------------------------------------------
# Groq implementation
# ---------------------------------------------------------------------------


class GroqProvider:
    """Wraps the Groq SDK (OpenAI-compatible API).

    Tool messages in our internal format carry a `tool_calls_json` field
    (set by the orchestrator) so we can reconstruct the required
    assistant→tool message pairs that the OpenAI-style API expects.
    """

    def __init__(self, api_key: str, model: str = "llama-3.1-70b-versatile") -> None:
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set")
        from groq import Groq

        self._client = Groq(api_key=api_key)
        self._model = model

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
    ) -> ProviderResponse:
        groq_messages: list[dict[str, Any]] = []

        if system:
            groq_messages.append({"role": "system", "content": system})

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "tool":
                tcj = msg.get("tool_calls_json")
                if tcj:
                    tc = json.loads(tcj)
                    # Groq requires a unique id that pairs the assistant tool_call
                    # with this tool result. Generate one deterministically.
                    call_id = f"call_{abs(hash(tcj)) % 0xFFFFFF:06x}"
                    groq_messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["args"]),
                            },
                        }],
                    })
                    groq_messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": content,
                    })
                else:
                    # Fallback for old history rows without tool_calls_json.
                    groq_messages.append({"role": "user", "content": f"Tool result: {content}"})
            else:
                groq_messages.append({"role": role, "content": content})

        groq_tools = None
        if tools:
            groq_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"],
                    },
                }
                for t in tools
            ]

        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=groq_messages,  # type: ignore[arg-type]
                tools=groq_tools,  # type: ignore[arg-type]
                tool_choice="auto" if groq_tools else None,
            )
        except Exception as e:  # noqa: BLE001
            raise ProviderError(str(e)) from e

        choice = resp.choices[0]
        msg_out = choice.message

        if msg_out.tool_calls:
            tool_calls = [
                ToolCall(
                    name=tc.function.name,
                    args=json.loads(tc.function.arguments),
                )
                for tc in msg_out.tool_calls
            ]
            return ProviderResponse(tool_calls=tool_calls)

        return ProviderResponse(text=msg_out.content or "")


class ProviderError(RuntimeError):
    """Wraps any underlying SDK / network error."""


# ---------------------------------------------------------------------------
# Mock implementation (for tests and demo rehearsal)
# ---------------------------------------------------------------------------


class MockProvider:
    """Deterministic stand-in. Picks a tool based on simple keyword matching,
    then returns a canned text answer on the next call.

    Behavior:
    - First call with a `tools` argument and no prior tool result → emit one tool call.
    - Subsequent call (after the tool result is appended) → emit a text answer.
    """

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
    ) -> ProviderResponse:
        latest = next((m for m in reversed(messages) if m["role"] == "user"), None)
        question = (latest or {}).get("content", "")
        tool_msgs = [m for m in messages if m["role"] == "tool"]

        # If we already ran a tool, summarize.
        if tool_msgs:
            payload = tool_msgs[-1]["content"]
            return ProviderResponse(
                text=(
                    f"Based on the tool result, here is what I found: {payload[:200]} "
                    f"(answer for: {question})."
                )
            )

        if not tools:
            return ProviderResponse(text=f"Echo: {question}")

        ql = question.lower()
        if any(w in ql for w in ["plot", "chart", "show me", "visualize", "graph"]):
            tool = "generate_chart"
            args = {"chart_type": "bar", "x": "category"}
        elif any(w in ql for w in ["statistic", "describe", "what does"]):
            tool = "get_column_statistics"
            args = {"column": "amt"}
        else:
            tool = "query_data"
            args = {"x": "category", "agg": "count"}
        return ProviderResponse(tool_calls=[ToolCall(name=tool, args=args)])


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_provider() -> LLMProvider:
    settings = get_settings()
    if settings.mock_llm:
        return MockProvider()
    name = settings.llm_provider.lower()
    if name == "gemini":
        model = settings.llm_model or "gemini-2.0-flash"
        return GeminiProvider(api_key=settings.gemini_api_key, model=model)
    if name == "groq":
        model = settings.llm_model or "llama-3.1-70b-versatile"
        return GroqProvider(api_key=settings.groq_api_key, model=model)
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


def serialize_tool_result(result: Any) -> str:
    """Convert a tool's return value to a JSON string the model can read."""
    return json.dumps(result, default=str)
