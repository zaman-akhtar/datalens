"""POST /api/upload — happy path, bad type, oversize."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient


def test_upload_valid_csv(client: TestClient, fixtures_dir: Path) -> None:
    csv = (fixtures_dir / "tiny.csv").read_bytes()
    r = client.post("/api/upload", files={"file": ("tiny.csv", csv, "text/csv")})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["n_rows"] == 5
    assert body["n_cols"] == 3
    assert body["original_filename"] == "tiny.csv"
    assert body["dataset_id"]


def test_upload_rejects_non_csv(client: TestClient) -> None:
    r = client.post(
        "/api/upload",
        files={"file": ("foo.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400
    assert "csv" in r.json()["detail"].lower()


def test_upload_rejects_oversize(
    client: TestClient, monkeypatch
) -> None:
    # Set the cap very low so we don't have to actually upload 50 MB.
    from app.config import reset_settings_for_tests

    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "1")
    reset_settings_for_tests()
    # Re-create app so the new setting is read
    from app.main import create_app

    big_app = create_app()
    big_client = TestClient(big_app)

    big = b"x" * (2 * 1024 * 1024)
    r = big_client.post("/api/upload", files={"file": ("big.csv", BytesIO(big), "text/csv")})
    assert r.status_code == 413
