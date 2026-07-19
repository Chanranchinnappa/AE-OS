"""pricing-math — granular COGS: exact token cost per task per agent.

DoD (03_AGENT_SPECS.md): cost-per-task figure updated after every
model-router change.

Cross-department rule (04_OPERATING_LOOP.md): this agent READS other
departments' work exclusively through Shared Memory (the Ledger) — it never
invokes another department directly. Deterministic SQL + arithmetic, zero
tokens (11_TOKEN_OPTIMIZATION.md Rule 5).
"""
from __future__ import annotations

from typing import Any

from departments.base import DepartmentAgent
from memory.registry import Registry

COST_RISE_FLAG_PCT = 20.0  # flag agents whose avg cost/task rose more than this


class PricingMath(DepartmentAgent):
    department = "CFO"
    name = "pricing-math"
    action_type = "cost_per_task_review"

    def execute(self, task: dict[str, Any], task_id: str) -> dict[str, Any]:
        rows = self.ledger.conn.execute(
            """SELECT agent_id,
                      SUM(CASE WHEN action_type='model_call' THEN cost_tokens ELSE 0 END) AS tokens,
                      SUM(cost_currency) AS currency,
                      SUM(CASE WHEN action_type!='model_call' THEN 1 ELSE 0 END) AS tasks
               FROM ledger
               WHERE agent_id NOT LIKE 'chairperson.%'
               GROUP BY agent_id"""
        ).fetchall()

        registry = Registry(self.ledger.conn, self.ledger)
        previous = registry.get("CFO", "cost_per_task") or {}

        report, flags = {}, []
        for r in rows:
            tasks = max(1, r["tasks"])
            per_task = round(r["tokens"] / tasks, 1)
            report[r["agent_id"]] = {
                "total_tokens": r["tokens"], "total_currency": r["currency"],
                "tasks": r["tasks"], "tokens_per_task": per_task,
            }
            prev = (previous.get(r["agent_id"]) or {}).get("tokens_per_task")
            if prev and prev > 0:
                rise_pct = (per_task - prev) / prev * 100
                if rise_pct > COST_RISE_FLAG_PCT:
                    flags.append({
                        "agent_id": r["agent_id"],
                        "previous_tokens_per_task": prev,
                        "current_tokens_per_task": per_task,
                        "rise_pct": round(rise_pct, 1),
                        "route_to": "rnd-hub optimization target "
                                    "(11_TOKEN_OPTIMIZATION.md Rule 6)",
                    })

        registry.set("CFO", "cost_per_task", report, self.agent_id)
        return {"cost_per_task": report, "cost_rise_flags": flags,
                "snapshot_written": True, "agents_reviewed": len(report)}

    def check_dod(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        notes = []
        if result.get("agents_reviewed", 0) == 0:
            notes.append("DoD fail: no agent activity found in Ledger to cost")
        if not result.get("snapshot_written"):
            notes.append("DoD fail: cost snapshot not written to Registry")
        for agent_id, row in result.get("cost_per_task", {}).items():
            if "tokens_per_task" not in row:
                notes.append(f"DoD fail: no cost-per-task figure for {agent_id}")
        if not notes:
            notes.append(
                f"DoD pass: cost-per-task computed for "
                f"{result['agents_reviewed']} agents, snapshot in Registry, "
                f"{len(result.get('cost_rise_flags', []))} cost-rise flags"
            )
        return (not any(n.startswith("DoD fail") for n in notes), notes)
