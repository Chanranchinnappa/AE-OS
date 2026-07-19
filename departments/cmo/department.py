"""CMO department head — runs the roster for one Operating Loop cycle.

Phase 1 scope (10_BUILD_ROADMAP.md): manually triggered, dry-run only. The CEO
orchestrator (Phase 2) will call run_cycle(); until then the Chairperson or a
Claude Code session triggers it directly.
"""
from __future__ import annotations

import uuid
from typing import Any

from core import kill_switch
from core.model_router import ModelRouter
from memory.ledger import Ledger
from memory.registry import Registry

from .seo_audit import SeoAudit
from .programmatic_seo import ProgrammaticSeo
from .ai_seo import AiSeo
from .cro_content import CroContent
from .ad_creative import AdCreative
from .mktg_psychology import MktgPsychology

AGENT_CLASSES = (SeoAudit, ProgrammaticSeo, AiSeo, CroContent,
                 AdCreative, MktgPsychology)


class CMODepartment:
    agent_id = "cmo.head"

    def __init__(self, ledger: Ledger | None = None,
                 router: ModelRouter | None = None,
                 registry: Registry | None = None):
        self.ledger = ledger or Ledger()
        self.router = router or ModelRouter(self.ledger)
        self.registry = registry or Registry(self.ledger.conn, self.ledger)
        self.agents = {cls.name: cls(self.ledger, self.router)
                       for cls in AGENT_CLASSES}

    def publish_roster(self) -> None:
        """Company Registry holds current-state truth: the live roster."""
        self.registry.set(
            "CMO", "roster",
            {name: agent.action_type for name, agent in self.agents.items()},
            self.agent_id,
        )

    @staticmethod
    def _hydrate(name: str, task: dict[str, Any]) -> dict[str, Any]:
        """Resolve allocation-level task specs into agent-ready inputs.

        The CEO allocates 'audit property X' by site root; turning that into
        parsed page records is CMO-internal work (site_inventory)."""
        if name == "seo-audit" and "pages" not in task and task.get("site_root"):
            from .site_inventory import inventory
            task = {**task, "pages": inventory(task["site_root"]),
                    "site": task.get("site", str(task["site_root"]))}
        return task

    def run_cycle(self, tasks: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Execute one department cycle: dispatch each task to its owning agent.

        `tasks` maps roster names (e.g. 'seo-audit') to task dicts. Unknown
        names fail loudly — never silently dropped (04_OPERATING_LOOP.md).
        """
        kill_switch.guard()
        cycle_id = str(uuid.uuid4())

        unknown = set(tasks) - set(self.agents)
        if unknown:
            raise ValueError(f"No CMO agent owns: {sorted(unknown)} "
                             "(see docs/03_AGENT_SPECS.md)")

        results = []
        for name, task in tasks.items():
            outcome = self.agents[name].run(self._hydrate(name, task))
            results.append(outcome)

        statuses = [r["status"] for r in results]
        costs = self.ledger.total_cost()
        summary = {
            "cycle_id": cycle_id,
            "dispatched": len(results),
            "success": statuses.count("success"),
            "failed": statuses.count("failed"),
            "needs_approval": statuses.count("needs_approval"),
            "cumulative_cost": costs,
        }
        self.ledger.log(
            department="CMO", agent_id=self.agent_id,
            action_type="cycle_summary",
            status="needs_approval" if summary["needs_approval"] else "success",
            inputs={"cycle_id": cycle_id, "tasks": sorted(tasks)},
            outputs=summary,
        )
        return {"summary": summary, "results": results}
