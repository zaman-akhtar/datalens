"""POST /api/upload — multipart CSV upload."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.db.session import get_conn
from app.models.upload import UploadAck
from app.services.ingest import ingest_csv

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadAck, status_code=status.HTTP_201_CREATED)
async def upload_csv(file: UploadFile = File(...)) -> UploadAck:  # noqa: B008
    settings = get_settings()

    # Filename / extension check
    filename = file.filename or "uploaded.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are accepted.",
        )

    # Stream read with size cap (count bytes; reject when exceeded)
    chunks: list[bytes] = []
    total = 0
    chunk_size = 1 * 1024 * 1024
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File exceeds {settings.max_upload_size_mb} MB cap.",
            )
        chunks.append(chunk)

    csv_bytes = b"".join(chunks)
    if not csv_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        with get_conn() as conn:
            dataset_id, n_rows, n_cols, sampled_from = ingest_csv(conn, csv_bytes, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return UploadAck(
        dataset_id=dataset_id,
        original_filename=filename,
        n_rows=n_rows,
        n_cols=n_cols,
        sampled_from=sampled_from,
    )
