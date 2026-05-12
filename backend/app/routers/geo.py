"""GET /api/datasets/{id}/geo — fraud count by region."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.session import get_conn
from app.services.profile import DatasetNotFoundError, build_profile, get_table_name

router = APIRouter(prefix="/api", tags=["geo"])

_STATE_HINTS = {"state", "region", "country", "province", "neighbourhood"}
_FRAUD_HINTS = {"is_fraud", "fraud", "is_fraudulent", "fraudulent"}


class GeoRow(BaseModel):
    state: str
    count: int
    fraud_count: int
    fraud_rate: float


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _find_col(profile: Any, hints: set[str]) -> str | None:
    for col in profile.columns:
        if col.safe_name.lower() in hints or col.name.lower() in hints:
            return col.safe_name
    return None


def geo_data(conn: sqlite3.Connection, dataset_id: str) -> list[dict[str, Any]]:
    profile = build_profile(conn, dataset_id)
    state_col = _find_col(profile, _STATE_HINTS)
    if state_col is None:
        return []

    table = get_table_name(conn, dataset_id)
    fraud_col = _find_col(profile, _FRAUD_HINTS)
    tq = _quote(table)
    sq = _quote(state_col)

    if fraud_col:
        fq = _quote(fraud_col)
        sql = (
            f"SELECT {sq} AS state, COUNT(*) AS cnt, "
            f"CAST(SUM(CASE WHEN {fq} IN (1, '1', 'true', 'True') THEN 1 ELSE 0 END) AS INTEGER) AS fraud_cnt "
            f"FROM {tq} WHERE {sq} IS NOT NULL "
            f"GROUP BY {sq} ORDER BY cnt DESC LIMIT 15"
        )
    else:
        sql = (
            f"SELECT {sq} AS state, COUNT(*) AS cnt, 0 AS fraud_cnt "
            f"FROM {tq} WHERE {sq} IS NOT NULL "
            f"GROUP BY {sq} ORDER BY cnt DESC LIMIT 15"
        )

    rows = conn.execute(sql).fetchall()
    return [
        {
            "state": r["state"],
            "count": int(r["cnt"]),
            "fraud_count": int(r["fraud_cnt"]),
            "fraud_rate": int(r["fraud_cnt"]) / int(r["cnt"]) if int(r["cnt"]) else 0.0,
        }
        for r in rows
    ]


@router.get("/datasets/{dataset_id}/geo", response_model=list[GeoRow])
def get_geo(dataset_id: str) -> list[GeoRow]:
    try:
        with get_conn() as conn:
            rows = geo_data(conn, dataset_id)
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found") from e
    return [GeoRow(**r) for r in rows]
