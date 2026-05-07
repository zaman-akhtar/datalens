"""Shared pytest fixtures.

We give every test a fresh on-disk SQLite DB inside a temp dir, so concurrency
doesn't bite and we still cover the real sqlite3 codepath rather than `:memory:`.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings_for_tests


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run each test against a fresh DB and a deterministic config."""
    db_path = tmp_path / "datalens.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "50")
    monkeypatch.setenv("DEBUG", "true")
    reset_settings_for_tests()
    yield
    reset_settings_for_tests()


@pytest.fixture()
def client() -> TestClient:
    # Import inside the fixture so config envs are applied first.
    from app.main import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture()
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture()
def conn():  # noqa: ANN201
    from app.db.session import get_conn

    with get_conn() as c:
        yield c
