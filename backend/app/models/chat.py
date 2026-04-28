"""Chat request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


class ToolCallRecord(BaseModel):
    name: str
    args: dict[str, Any]
    result_preview: str = Field(description="First ~500 chars of the tool's JSON result.")


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    tool_calls: list[ToolCallRecord]
    partial: bool = Field(default=False, description="True if max tool iterations was hit.")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "tool"]
    content: str
    created_at: datetime
