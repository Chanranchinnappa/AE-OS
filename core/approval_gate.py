"""Approval Gate — 08_GOVERNANCE_AND_SAFETY.md Approval Gate Matrix.

Any department requesting real spend passes through here, never around it.
Spend within the configured ceiling is logged and proceeds autonomously.
Spend above ceiling — and every action in ALWAYS_GATED — is never
auto-approved: it halts as `needs_approval` and creates an approval record
for the Chairperson (06_MEMORY_SYSTEM.md `approvals` table).

Decisions are made ONLY via the Chairperson CLI; no agent or CEO code path
may call decide():
    python -m core.approval_gate list
    python -m core.approval_gate approve <approval_id>
    python -m core.approval_gate reject  <approval_id>
"""
from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from memory.ledger import Ledger
from . import kill_switch

# Always gated regardless of amount (08_GOVERNANCE_AND_SAFETY.md matrix).
ALWAYS_GATED = {
    "production_deploy",
    "new_department",
    "architecture_change",
    "contract_signature",
    "trading_cap_increase",
    "loophole_execution",
}


class ApprovalError(Exception):
    pass

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "settings.json"


@dataclass
class SpendDecision:
    approved: bool
    status: str  # 'success' (auto-approved, logged) or 'needs_approval'
    ceiling: float
    requested: float
    approval_id: str | None = None


def _daily_marketing_ceiling() -> float:
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text())
        return float(cfg.get("budget_ceilings", {}).get("daily_marketing_spend", 0))
    return 0.0


def request_spend(
    amount: float,
    purpose: str,
    department: str,
    agent_id: str,
    ledger: Ledger | None = None,
) -> SpendDecision:
    """Check a spend request against the ceiling. Never auto-approves above it."""
    kill_switch.guard()
    ledger = ledger or Ledger()
    ceiling = _daily_marketing_ceiling()

    if amount <= ceiling:
        ledger.log(
            department=department, agent_id=agent_id,
            action_type="spend_request", status="success",
            inputs={"amount": amount, "purpose": purpose},
            outputs={"ceiling": ceiling, "auto_approved": True},
            cost_currency=amount,
        )
        return SpendDecision(approved=True, status="success",
                             ceiling=ceiling, requested=amount)

    approval_id = str(uuid.uuid4())
    ledger.conn.execute(
        "INSERT INTO approvals (id, requested_at, action, reason) VALUES (?,?,?,?)",
        (approval_id, datetime.now(timezone.utc).isoformat(),
         f"spend:{purpose}", f"Requested {amount} exceeds ceiling {ceiling}"),
    )
    ledger.conn.commit()
    ledger.log(
        department=department, agent_id=agent_id,
        action_type="spend_request", status="needs_approval",
        inputs={"amount": amount, "purpose": purpose},
        outputs={"ceiling": ceiling, "auto_approved": False},
        approval_ref=approval_id,
    )
    return SpendDecision(approved=False, status="needs_approval",
                         ceiling=ceiling, requested=amount, approval_id=approval_id)


def requires_approval(action: str, amount: float = 0.0) -> bool:
    """The matrix: does this action halt for the Chairperson?"""
    if action in ALWAYS_GATED:
        return True
    if action == "spend":
        return amount > _daily_marketing_ceiling()
    return False


class ApprovalGate:
    """Request/track/decide workflow over the `approvals` table."""

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()
        self.conn = self.ledger.conn

    def request(self, action: str, reason: str, department: str,
                agent_id: str) -> str:
        """File an approval request; returns approval_id. Caller MUST halt the
        gated action until status() returns 'approved'."""
        approval_id = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO approvals (id, requested_at, action, reason) VALUES (?,?,?,?)",
            (approval_id, datetime.now(timezone.utc).isoformat(), action, reason),
        )
        self.conn.commit()
        self.ledger.log(
            department=department, agent_id=agent_id,
            action_type="approval_request", status="needs_approval",
            inputs={"action": action}, outputs={"reason": reason},
            approval_ref=approval_id,
        )
        return approval_id

    def status(self, approval_id: str) -> str:
        row = self.conn.execute(
            "SELECT decision FROM approvals WHERE id=?", (approval_id,)
        ).fetchone()
        if row is None:
            raise ApprovalError(f"Unknown approval id: {approval_id}")
        return row["decision"] or "pending"

    def pending(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM approvals WHERE decision IS NULL ORDER BY requested_at"
        ).fetchall()]

    def decide(self, approval_id: str, decision: str,
               decided_by: str = "chairperson") -> None:
        """Record the Chairperson's decision. Chairperson CLI/interface only —
        agents and the CEO never call this; every decision is Ledger-logged."""
        if decision not in ("approved", "rejected"):
            raise ApprovalError(f"Invalid decision: {decision}")
        if self.status(approval_id) != "pending":
            raise ApprovalError(f"Approval {approval_id} already decided")
        self.conn.execute(
            "UPDATE approvals SET decision=?, decided_at=? WHERE id=?",
            (decision, datetime.now(timezone.utc).isoformat(), approval_id),
        )
        self.conn.commit()
        self.ledger.log(
            department="CEO", agent_id=f"chairperson.{decided_by}",
            action_type="approval_decision", status="success",
            inputs={"approval_id": approval_id}, outputs={"decision": decision},
            approval_ref=approval_id,
        )


def _cli() -> int:
    gate = ApprovalGate()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        rows = gate.pending()
        if not rows:
            print("No pending approvals.")
        for r in rows:
            print(f"{r['id']}  [{r['action']}]  {r['reason']}")
    elif cmd in ("approve", "reject"):
        if len(sys.argv) < 3:
            print("Usage: python -m core.approval_gate approve|reject <approval_id>")
            return 1
        gate.decide(sys.argv[2], "approved" if cmd == "approve" else "rejected")
        print(f"{cmd}{'d' if cmd == 'approve' else 'ed'}: {sys.argv[2]}")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
