"""Company Registry — Tier 2 memory: current-state truth.

Per 06_MEMORY_SYSTEM.md: overwritten in place as state changes, but every
overwrite is mirrored to the Ledger as a diff. Only the owning department
may write to its own section; any agent may read any section.

Never store raw secrets here — references to the secrets manager only.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from . import db as _db
from .ledger import Ledger, LedgerError

SECRET_HINTS = ("api_key", "apikey", "secret", "password", "token", "private_key")


class RegistryError(Exception):
    pass


class Registry:
    def __init__(self, conn=None, ledger: Ledger | None = None):
        self.conn = conn or _db.connect()
        self.ledger = ledger or Ledger(self.conn)

    def get(self, department: str, key: str) -> Any | None:
        row = self.conn.execute(
            "SELECT value FROM registry WHERE department=? AND key=?",
            (department.upper(), key),
        ).fetchone()
        return json.loads(row["value"]) if row else None

    def set(self, department: str, key: str, value: Any, writer_agent_id: str) -> None:
        department = department.upper()
        if department not in _db.DEPARTMENTS:
            raise RegistryError(f"Unknown department: {department}")

        # Access rule: only the owning department writes its own section.
        writer_dept = writer_agent_id.split(".")[0].upper()
        if writer_dept != department:
            raise RegistryError(
                f"{writer_agent_id} may not write to {department}'s registry section"
            )

        # Crude secret guard — real enforcement is 'never put secrets here' discipline.
        flat = json.dumps(value).lower()
        for hint in SECRET_HINTS:
            if f'"{hint}"' in flat:
                raise RegistryError(
                    f"Registry must not hold raw secrets (found key hint: {hint}). "
                    "Store a secrets-manager reference instead."
                )

        old = self.get(department, key)
        self.conn.execute(
            """INSERT INTO registry (department, key, value, updated_at)
               VALUES (?,?,?,?)
               ON CONFLICT(department, key) DO UPDATE
               SET value=excluded.value, updated_at=excluded.updated_at""",
            (department, key, json.dumps(value),
             datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

        # Mirror the overwrite to the Ledger as a diff.
        self.ledger.log(
            department=department,
            agent_id=writer_agent_id,
            action_type="registry_update",
            status="success",
            inputs={"key": key, "old": old},
            outputs={"key": key, "new": value},
        )
