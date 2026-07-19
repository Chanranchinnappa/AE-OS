"""AE-OS bootstrap memory layer — SQLite.

Per 06_MEMORY_SYSTEM.md: SQLite for bootstrap, migrate to Postgres(+pgvector)/Cognee
when volume justifies it. Three tiers: Ephemera / Company Registry / Ledger.

The Ledger is append-only. SQLite triggers physically block UPDATE and DELETE,
so immutability is enforced by the database, not by convention.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# AE_OS_DB_PATH overrides the default location (tests, alternate deployments).
DB_PATH = Path(os.environ.get(
    "AE_OS_DB_PATH",
    Path(__file__).resolve().parent.parent / "data" / "ae_os.db",
))

DEPARTMENTS = ("CMO", "CRO", "CFO", "CDO", "COO", "LEGAL", "TRADING", "RND", "CEO")

SCHEMA = """
CREATE TABLE IF NOT EXISTS ledger (
    id            TEXT PRIMARY KEY,            -- uuid4
    timestamp     TEXT NOT NULL,               -- UTC ISO-8601
    department    TEXT NOT NULL CHECK (department IN
                    ('CMO','CRO','CFO','CDO','COO','LEGAL','TRADING','RND','CEO')),
    agent_id      TEXT NOT NULL,               -- e.g. 'cmo.seo-audit'
    action_type   TEXT NOT NULL,
    inputs        TEXT NOT NULL DEFAULT '{}',  -- JSON
    outputs       TEXT NOT NULL DEFAULT '{}',  -- JSON, includes artifact links
    cost_tokens   INTEGER NOT NULL DEFAULT 0,
    cost_currency REAL NOT NULL DEFAULT 0.0,
    status        TEXT NOT NULL CHECK (status IN ('success','failed','needs_approval')),
    approval_ref  TEXT,                        -- links to Chairperson decision record
    corrects      TEXT REFERENCES ledger(id)   -- corrections append, never overwrite
);

-- Immutability: the Ledger is append-only, enforced at the DB level.
CREATE TRIGGER IF NOT EXISTS ledger_no_update
BEFORE UPDATE ON ledger
BEGIN SELECT RAISE(ABORT, 'Ledger is append-only: UPDATE forbidden'); END;

CREATE TRIGGER IF NOT EXISTS ledger_no_delete
BEFORE DELETE ON ledger
BEGIN SELECT RAISE(ABORT, 'Ledger is append-only: DELETE forbidden'); END;

CREATE INDEX IF NOT EXISTS idx_ledger_ts    ON ledger(timestamp);
CREATE INDEX IF NOT EXISTS idx_ledger_dept  ON ledger(department);
CREATE INDEX IF NOT EXISTS idx_ledger_agent ON ledger(agent_id);

-- Tier 2: Company Registry — current-state truth, one JSON doc per (department, key).
-- Overwrites are mirrored to the Ledger as diffs by registry.py.
CREATE TABLE IF NOT EXISTS registry (
    department TEXT NOT NULL,
    key        TEXT NOT NULL,
    value      TEXT NOT NULL,        -- JSON
    updated_at TEXT NOT NULL,
    PRIMARY KEY (department, key)
);

-- Tier 1: Ephemera — TTL-based scratch, archived to Ledger before expiry.
CREATE TABLE IF NOT EXISTS ephemera (
    id         TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    agent_id   TEXT NOT NULL,
    content    TEXT NOT NULL,        -- JSON
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

-- Chairperson approval records (referenced by ledger.approval_ref).
CREATE TABLE IF NOT EXISTS approvals (
    id           TEXT PRIMARY KEY,
    requested_at TEXT NOT NULL,
    action       TEXT NOT NULL,
    reason       TEXT NOT NULL,
    decided_at   TEXT,
    decision     TEXT CHECK (decision IN ('approved','rejected') OR decision IS NULL)
);
"""


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open (and initialize if needed) the AE-OS database."""
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
