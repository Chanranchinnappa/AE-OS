"""Ledger logging middleware.

Per 06_MEMORY_SYSTEM.md access rules: only this middleware writes to the Ledger,
never an agent directly. Guarantees consistent schema and prevents tampering.

Per 00_MASTER_PROMPT.md: "Always write to the Ledger before marking a task
complete — untracked work does not count as done."
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from . import db as _db

VALID_STATUS = ("success", "failed", "needs_approval")


class LedgerError(Exception):
    pass


class Ledger:
    """The only sanctioned write path to the append-only Ledger."""

    def __init__(self, conn=None):
        self.conn = conn or _db.connect()

    def log(
        self,
        department: str,
        agent_id: str,
        action_type: str,
        status: str,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        cost_tokens: int = 0,
        cost_currency: float = 0.0,
        approval_ref: str | None = None,
        corrects: str | None = None,
    ) -> str:
        """Append one entry. Returns the entry id."""
        department = department.upper()
        if department not in _db.DEPARTMENTS:
            raise LedgerError(f"Unknown department: {department}")
        if status not in VALID_STATUS:
            raise LedgerError(f"Invalid status: {status}")
        if not agent_id or not action_type:
            raise LedgerError("agent_id and action_type are required")

        entry_id = str(uuid.uuid4())
        self.conn.execute(
            """INSERT INTO ledger
               (id, timestamp, department, agent_id, action_type, inputs, outputs,
                cost_tokens, cost_currency, status, approval_ref, corrects)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                entry_id,
                datetime.now(timezone.utc).isoformat(),
                department,
                agent_id,
                action_type,
                json.dumps(inputs or {}),
                json.dumps(outputs or {}),
                int(cost_tokens),
                float(cost_currency),
                status,
                approval_ref,
                corrects,
            ),
        )
        self.conn.commit()
        return entry_id

    def correct(self, original_id: str, **kwargs) -> str:
        """Corrections are appended as new entries referencing the old one."""
        row = self.conn.execute(
            "SELECT id FROM ledger WHERE id=?", (original_id,)
        ).fetchone()
        if row is None:
            raise LedgerError(f"Cannot correct unknown entry {original_id}")
        return self.log(corrects=original_id, **kwargs)

    def recent(self, n: int = 10, department: str | None = None) -> list[dict]:
        """Targeted reads only (11_TOKEN_OPTIMIZATION.md Rule 1) — never dump history."""
        q = "SELECT * FROM ledger"
        args: list = []
        if department:
            q += " WHERE department=?"
            args.append(department.upper())
        q += " ORDER BY timestamp DESC LIMIT ?"
        args.append(n)
        return [dict(r) for r in self.conn.execute(q, args).fetchall()]

    def total_cost(self) -> dict:
        row = self.conn.execute(
            "SELECT COALESCE(SUM(cost_tokens),0) t, COALESCE(SUM(cost_currency),0) c FROM ledger"
        ).fetchone()
        return {"tokens": row["t"], "currency": row["c"]}
