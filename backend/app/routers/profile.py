"""Profile endpoints — list datasets, fetch one profile."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db.session import get_conn
from app.models.dataset import DatasetProfile, DatasetSummary
from app.services.profile import DatasetNotFoundError, build_profile, list_datasets

router = APIRouter(prefix="/api", tags=["profile"])


@router.get("/datasets", response_model=list[DatasetSummary])
def get_datasets() -> list[DatasetSummary]:
    with get_conn() as conn:
        return list_datasets(conn)


@router.get("/datasets/{dataset_id}/profile", response_model=DatasetProfile)
def get_profile(dataset_id: str) -> DatasetProfile:
    try:
        with get_conn() as conn:
            return build_profile(conn, dataset_id)
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found") from e
