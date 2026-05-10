"""SQLite connection helper.

We use the sqlite3 stdlib rather than SQLAlchemy because (a) ADR-003 pushes us
toward dynamic per-dataset tables and (b) parametrized queries via `?` placeholders
are exactly what the safe query builder needs.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.config import get_settings


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _connect(path: Path) -> sqlite3.Connection:
    _ensure_parent(path)
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Context manager yielding a fresh sqlite3.Connection.

    Each request gets its own connection. SQLite is fine with this for our load.
    """
    settings = get_settings()
    conn = _connect(settings.db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
