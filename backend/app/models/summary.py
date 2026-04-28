"""Executive-summary schema."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Summary(BaseModel):
    dataset_id: str
    text: str
    generated_at: datetime
