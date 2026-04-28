"""Error envelope used across all 4xx/5xx responses."""
from __future__ import annotations

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    hint: str | None = None
