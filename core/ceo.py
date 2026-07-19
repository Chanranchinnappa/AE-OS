"""AI CEO orchestrator — Phase 2 (10_BUILD_ROADMAP.md).

Implements the Operating Loop steps the CEO owns (04_OPERATING_LOOP.md):
ingestion, allocation, dispatch, verification aggregation, and compilation
of the persona-wrapped executive brief. Persona/tone rules live alongside in
`ceo.md`; the Prime Directive stays canonical in docs/00_MASTER_PROMPT.md.

Bootstrap allocation is deterministic rules, not an LLM call — the CEO
spends tokens on department work, not on deciding to do the obvious
(11_TOKEN_OPTIMIZATION.md Rule 5).

CLI:
    python -m core.ceo cycle      # one full dry-run Operating Loop cycle
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from departments.cfo import PricingMath
from departments.cmo import CMODepartment
from departments.coo import LaunchRunbook
from memory.ledger import Ledger
from memory.registry import Registry

from . import kill_switch
from .approval_gate import ApprovalGate
from .model_router import ModelRouter

REPO_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = REPO_ROOT / "config" / "settings.json"


def _settings() -> dict:
    return json.loads(SETTINGS_PATH.read_text()) if SETTINGS_PATH.exists() else {}


class CEO:
    agent_id = "ceo.orchestrator"
    department = "CEO"

    def __init__(self, ledger: Ledger | None = None,
                 router: ModelRouter | None = None):
        self.ledger = ledger or Ledger()
        self.router = router or ModelRouter(self.ledger)
        self.registry = Registry(self.ledger.conn, self.ledger)
        self.gate = ApprovalGate(self.ledger)
        self.cmo = CMODepartment(self.ledger, self.router)
        self.coo_agents = {"launch-runbook": LaunchRunbook(self.ledger, self.router)}
        self.cfo_agents = {"pricing-math": PricingMath(self.ledger, self.router)}

    # Step 1 — Ingestion
    def ingest(self) -> dict[str, Any]:
        cfg = _settings()
        return {
            "recent_ledger": self.ledger.recent(20),
            "pending_approvals": self.gate.pending(),
            "kill_switch": kill_switch.status(),
            "properties": cfg.get("venture", {}).get("properties", []),
            "cost_baseline": self.ledger.total_cost(),
        }

    # Step 2 — Allocation (deterministic bootstrap rules)
    def allocate(self, snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
        cmo_tasks: dict[str, Any] = {}
        for prop in snapshot["properties"]:
            root = REPO_ROOT / prop.get("root", "")
            if prop.get("root") and root.is_dir():
                cmo_tasks["seo-audit"] = {
                    "site": prop["name"], "site_root": str(root),
                    "priority": "P1",
                }
        allocations: dict[str, dict[str, Any]] = {}
        if cmo_tasks:
            allocations["CMO"] = cmo_tasks

        # COO: prepare the deploy runbook for each in-build property — but
        # never file a duplicate approval while one is already pending.
        pending_deploys = [p["reason"] for p in snapshot["pending_approvals"]
                           if p["action"] == "production_deploy"]
        coo_tasks: dict[str, Any] = {}
        for prop in snapshot["properties"]:
            if prop.get("status") == "in_build" and not any(
                    prop["name"] in reason for reason in pending_deploys):
                coo_tasks["launch-runbook"] = {
                    "product": prop["name"], "property": prop, "priority": "P1",
                }
        if coo_tasks:
            allocations["COO"] = coo_tasks

        # CFO cost review runs every cycle once any Ledger activity exists.
        allocations["CFO"] = {"pricing-math": {"priority": "P2"}}
        return allocations

    # Step 3+4 — Dispatch & verification aggregation. CFO runs AFTER CMO so
    # pricing-math sees this cycle's Ledger entries (handoff via Shared
    # Memory, never a direct call).
    def dispatch(self, allocations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        if "CMO" in allocations:
            cmo_out = self.cmo.run_cycle(allocations["CMO"])
            results.extend(cmo_out["results"])
        for name, task in allocations.get("COO", {}).items():
            results.append(self.coo_agents[name].run(task))
        for name, task in allocations.get("CFO", {}).items():
            results.append(self.cfo_agents[name].run(task))
        return results

    # Step 7 — Compilation (persona rules in ceo.md; deterministic, 0 tokens)
    def compile_brief(self, snapshot: dict[str, Any],
                      results: list[dict[str, Any]],
                      cost_before: dict[str, Any]) -> str:
        cost_now = self.ledger.total_cost()
        cycle_tokens = cost_now["tokens"] - cost_before["tokens"]
        cycle_currency = cost_now["currency"] - cost_before["currency"]
        ok = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "failed"]
        halted = [r for r in results if r["status"] == "needs_approval"]
        pending = self.gate.pending()

        lines = [
            f"AE-OS Executive Brief — {datetime.now(timezone.utc).date().isoformat()}",
            "Revenue: no revenue data yet — no property is live; "
            "no numbers will be invented.",
            f"Cost this cycle: {cycle_tokens} tokens, {cycle_currency:.2f} "
            f"currency (cumulative {cost_now['tokens']} / "
            f"{cost_now['currency']:.2f}).",
            f"Dispatched {len(results)} agent tasks: {len(ok)} passed DoD, "
            f"{len(failed)} failed, {len(halted)} halted for approval.",
        ]
        for r in failed:
            lines.append(f"FAILED {r['agent_id']}: {r['dod_notes'][0][:80]}")
        if pending:
            lines.append(f"Blockers needing you: {len(pending)} pending "
                         "approval(s) — `python -m core.approval_gate list`.")
        if pending:
            action = "Decide the pending approvals; everything else proceeds."
        elif failed:
            action = f"Review the {len(failed)} DoD failure(s) logged this cycle."
        else:
            action = ("Advance the roadmap: next unbuilt Phase 2 item "
                      "(third department / interface).")
        lines.append(f"Recommended next action: {action}")

        brief = "\n".join(lines)
        max_words = _settings().get("chairperson", {}).get("report_max_words", 200)
        words = brief.split()
        if len(words) > max_words:
            brief = " ".join(words[:max_words]) + " [truncated at word cap]"
        return brief

    # The full loop (Steps 1-8; RnD review arrives in Phase 4)
    def run_cycle(self) -> dict[str, Any]:
        kill_switch.guard()
        cycle_id = str(uuid.uuid4())
        snapshot = self.ingest()
        cost_before = snapshot["cost_baseline"]
        allocations = self.allocate(snapshot)
        results = self.dispatch(allocations)
        brief = self.compile_brief(snapshot, results, cost_before)

        statuses = [r["status"] for r in results]
        self.ledger.log(
            department=self.department, agent_id=self.agent_id,
            action_type="operating_loop_cycle",
            status="needs_approval" if "needs_approval" in statuses else "success",
            inputs={"cycle_id": cycle_id,
                    "allocations": {d: sorted(t) for d, t in allocations.items()}},
            outputs={"statuses": statuses, "brief": brief},
        )
        return {"cycle_id": cycle_id, "allocations": allocations,
                "results": results, "brief": brief}


def _cli() -> int:
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "cycle"
    if cmd != "cycle":
        print(__doc__)
        return 1
    out = CEO().run_cycle()
    print(out["brief"])
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
