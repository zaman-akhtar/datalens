"""Chat orchestrator — runs the LLM tool-use loop and persists messages."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any

from app.config import get_settings
from app.models.chat import ChatMessage, ChatResponse, ToolCallRecord
from app.services.llm.provider import (
    LLMProvider,
    ProviderResponse,
    get_provider,
    serialize_tool_result,
)
from app.services.llm.tools import TOOL_FUNCTIONS, TOOL_SCHEMAS
from app.services.profile import build_profile

_SYSTEM_BASE = (
    "You are DataLens, a data analytics assistant. The user has uploaded a CSV dataset.\n"
    "Available columns:\n{columns}\n\n"
    "You have three tools:\n"
    "  • query_data — run aggregations (count/sum/mean/min/max grouped by a column)\n"
    "  • get_column_statistics — descriptive stats for one column\n"
    "  • generate_chart — return a chart spec the UI will render\n\n"
    "Rules: use at most {max} tool calls per reply. When you have enough information, "
    "answer in one concise paragraph and cite the key numbers you found. "
    "Always refer to columns by their exact safe_name shown above."
)


def _persist(
    conn: sqlite3.Connection,
    dataset_id: str,
    conversation_id: str,
    role: str,
    content: str,
    tool_calls_json: str | None = None,
) -> None:
    conn.execute(
        """INSERT INTO chat_messages
           (dataset_id, conversation_id, role, content, tool_calls_json)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, conversation_id, role, content, tool_calls_json),
    )


def load_history(conn: sqlite3.Connection, dataset_id: str) -> list[ChatMessage]:
    rows = conn.execute(
        """SELECT role, content, created_at FROM chat_messages
           WHERE dataset_id = ?
           ORDER BY id ASC""",
        (dataset_id,),
    ).fetchall()
    out: list[ChatMessage] = []
    for r in rows:
        ts = r["created_at"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace(" ", "T"))
        out.append(ChatMessage(role=r["role"], content=r["content"], created_at=ts))
    return out


def chat_turn(
    conn: sqlite3.Connection,
    dataset_id: str,
    user_message: str,
    conversation_id: str | None = None,
    provider: LLMProvider | None = None,
) -> ChatResponse:
    """Run a single user → assistant turn with up to N tool iterations."""
    settings = get_settings()
    provider = provider or get_provider()
    conv_id = conversation_id or uuid.uuid4().hex[:16]

    _persist(conn, dataset_id, conv_id, "user", user_message)

    # Build the messages array (we keep it simple — full history per turn for MVP).
    history_rows = conn.execute(
        """SELECT role, content, tool_calls_json FROM chat_messages
           WHERE dataset_id = ? AND conversation_id = ?
           ORDER BY id ASC""",
        (dataset_id, conv_id),
    ).fetchall()
    messages: list[dict[str, Any]] = [
        {
            "role": r["role"],
            "content": r["content"],
            **({"tool_calls_json": r["tool_calls_json"]} if r["tool_calls_json"] else {}),
        }
        for r in history_rows
    ]

    # Build system prompt with schema so the LLM knows column names upfront.
    profile = build_profile(conn, dataset_id)
    col_lines = "\n".join(
        f"  - {c.safe_name} ({c.dtype}, {c.n_unique} unique values)"
        + (f" — original name: '{c.name}'" if c.name != c.safe_name else "")
        for c in profile.columns
        if not c.is_index
    )
    system = _SYSTEM_BASE.format(columns=col_lines, max=settings.max_tool_iterations)

    tool_records: list[ToolCallRecord] = []
    max_iters = settings.max_tool_iterations
    final_text = ""
    partial = False

    for i in range(max_iters + 1):
        resp: ProviderResponse = provider.generate(
            messages=messages, tools=TOOL_SCHEMAS, system=system
        )
        if resp.is_tool_call:
            assert resp.tool_calls
            for call in resp.tool_calls:
                fn = TOOL_FUNCTIONS.get(call.name)
                if fn is None:
                    tool_result = {"error": f"Unknown tool: {call.name}"}
                else:
                    try:
                        tool_result = fn(conn, dataset_id, **call.args)  # type: ignore[arg-type]
                    except TypeError as e:
                        tool_result = {"error": f"Bad args: {e}"}
                serialized = serialize_tool_result(tool_result)
                tool_records.append(
                    ToolCallRecord(
                        name=call.name,
                        args=call.args,
                        result_preview=serialized[:500],
                    )
                )
                _persist(
                    conn,
                    dataset_id,
                    conv_id,
                    "tool",
                    serialized,
                    tool_calls_json=json.dumps({"name": call.name, "args": call.args}),
                )
                messages.append({
                    "role": "tool",
                    "content": serialized,
                    "tool_calls_json": json.dumps({"name": call.name, "args": call.args}),
                })
            if i == max_iters - 1:
                # Used last allowed iteration on a tool — flag partial.
                partial = True
                final_text = "I ran out of tool budget; here's what I found so far."
                break
            continue

        # Text answer
        final_text = resp.text or ""
        break
    else:
        partial = True
        final_text = "Reached maximum reasoning steps."

    _persist(conn, dataset_id, conv_id, "assistant", final_text)

    return ChatResponse(
        answer=final_text,
        conversation_id=conv_id,
        tool_calls=tool_records,
        partial=partial,
    )
