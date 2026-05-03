"""Executive summary endpoint."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db.session import get_conn
from app.models.summary import Summary
from app.services.llm.summary_prompt import generate_summary
from app.services.profile import DatasetNotFoundError

router = APIRouter(prefix="/api/datasets", tags=["summary"])


@router.get("/{dataset_id}/summary", response_model=Summary)
def get_summary(dataset_id: str, refresh: bool = False) -> Summary:
    try:
        with get_conn() as conn:
            return generate_summary(conn, dataset_id, refresh=refresh)
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found") from e
