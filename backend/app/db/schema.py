"""Catalog schema (ADR-003).

`datasets` lists every uploaded CSV; one physical `dataset_<id>` table is created
per upload by `services/ingest.py`.
"""
from __future__ import annotations

import sqlite3

CATALOG_DDL = """
CREATE TABLE IF NOT EXISTS datasets (
    id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    table_name TEXT NOT NULL UNIQUE,
    n_rows INTEGER NOT NULL,
    n_cols INTEGER NOT NULL,
    column_meta_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant','tool')),
    content TEXT NOT NULL,
    tool_calls_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_dataset
    ON chat_messages(dataset_id, conversation_id, created_at);

CREATE TABLE IF NOT EXISTS summaries (
    dataset_id TEXT PRIMARY KEY REFERENCES datasets(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    """Create catalog tables if missing. Safe to call repeatedly."""
    conn.executescript(CATALOG_DDL)
