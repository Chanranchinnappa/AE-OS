"""Generic department sub-agent base — the contract every AE-OS agent obeys.

Non-negotiables enforced here for every department (CLAUDE.md):
  1. `core.kill_switch.guard()` before acting.
  2. All LLM calls through `ModelRouter.route()` (free-tier-first).
  3. Definition of Done (03_AGENT_SPECS.md) checked before logging.
  4. Ledger write via `memory.ledger.Ledger` before returning.
  5. System prompt lives in a `.md` file alongside each agent module.
"""
from __future__ import annotations

import sys
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from core import kill_switch
from core.model_router import ModelRouter
from memory.ledger import Ledger


class DepartmentAgent(ABC):
    #: Ledger department enum value, e.g. "CMO", "CFO"
    department: str = ""
    #: roster name from 03_AGENT_SPECS.md, e.g. "seo-audit"
    name: str = ""
    #: ledger action_type for this agent's primary action
    action_type: str = ""

    def __init__(self, ledger: Ledger | None = None, router: ModelRouter | None = None):
        self.ledger = ledger or Ledger()
        self.router = router or ModelRouter(self.ledger)

    @property
    def agent_id(self) -> str:
        return f"{self.department.lower()}.{self.name}"

    def system_prompt(self) -> str:
        """Prompt file sits alongside the module: seo_audit.py -> seo_audit.md."""
        module_file = Path(sys.modules[self.__class__.__module__].__file__)
        return module_file.with_suffix(".md").read_text(encoding="utf-8")

    def draft(self, prompt: str, task_id: str, task_class: str = "routine") -> str:
        """All text generation routes through the ModelRouter (Tier 0 first)."""
        full = f"{self.system_prompt()}\n\n---\n{prompt}"
        return self.router.route(
            full, agent_id=self.agent_id, department=self.department,
            task_id=task_id, task_class=task_class,
        ).text

    @abstractmethod
    def execute(self, task: dict[str, Any], task_id: str) -> dict[str, Any]:
        """Do the work. Return a structured result dict."""

    @abstractmethod
    def check_dod(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify the result against this agent's Definition of Done."""

    def run(self, task: dict[str, Any] | None = None) -> dict[str, Any]:
        """Guard -> execute -> DoD check -> Ledger log -> return."""
        kill_switch.guard()
        task = task or {}
        task_id = task.get("task_id") or str(uuid.uuid4())

        result = self.execute(task, task_id)

        dod_ok, dod_notes = self.check_dod(result)
        if result.get("requires_approval"):
            status = "needs_approval"   # money-moving actions halt for the Chairperson
        elif dod_ok:
            status = "success"
        else:
            status = "failed"

        entry_id = self.ledger.log(
            department=self.department,
            agent_id=self.agent_id,
            action_type=self.action_type,
            status=status,
            inputs={"task_id": task_id, **{k: v for k, v in task.items() if k != "task_id"}},
            outputs={"result": result, "dod_notes": dod_notes},
        )
        return {
            "agent_id": self.agent_id,
            "task_id": task_id,
            "status": status,
            "dod_notes": dod_notes,
            "ledger_id": entry_id,
            "result": result,
        }
