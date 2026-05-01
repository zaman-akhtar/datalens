"""POST /api/datasets/{id}/query plus GET /api/datasets/{id}/charts."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db.session import get_conn
from app.models.chart import ChartSpec
from app.models.query import QueryRequest, QueryResult
from app.services.chart_picker import pick_charts
from app.services.profile import DatasetNotFoundError, build_profile
from app.services.query_engine import UnknownColumnError, run_query

router = APIRouter(prefix="/api/datasets", tags=["query"])


@router.get("/{dataset_id}/charts", response_model=list[ChartSpec])
def get_chart_picks(dataset_id: str) -> list[ChartSpec]:
    try:
        with get_conn() as conn:
            profile = build_profile(conn, dataset_id)
            return pick_charts(profile)
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found") from e


@router.post("/{dataset_id}/query", response_model=QueryResult)
def post_query(dataset_id: str, request: QueryRequest) -> QueryResult:
    try:
        with get_conn() as conn:
            return run_query(conn, dataset_id, request)
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found") from e
    except UnknownColumnError as e:
        raise HTTPException(status_code=400, detail=f"Unknown column: {e}") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
