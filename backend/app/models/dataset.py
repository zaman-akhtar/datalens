"""Dataset catalog and column-profile schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DType = Literal["numeric", "categorical", "datetime", "boolean", "text"]


class ColumnProfile(BaseModel):
    name: str = Field(description="Display name as it appears in the original CSV header.")
    safe_name: str = Field(description="Sanitized name used in the SQLite table.")
    dtype: DType
    null_pct: float = Field(ge=0.0, le=1.0)
    n_unique: int
    sample_values: list[str | int | float | bool | None] = Field(max_length=5)
    is_index: bool = False
    # Numeric-only fields (None for other dtypes)
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    skew: float | None = None


class DatasetSummary(BaseModel):
    """Lightweight catalog entry for sidebars."""

    dataset_id: str
    original_filename: str
    n_rows: int
    n_cols: int
    created_at: datetime


class DatasetProfile(BaseModel):
    dataset_id: str
    original_filename: str
    n_rows: int
    n_cols: int
    columns: list[ColumnProfile]
    created_at: datetime
