"""Upload acknowledgement schema."""
from __future__ import annotations

from pydantic import BaseModel, Field


class UploadAck(BaseModel):
    dataset_id: str = Field(description="ULID-like opaque ID used in /api/datasets/{id}/* URLs.")
    original_filename: str
    n_rows: int
    n_cols: int
