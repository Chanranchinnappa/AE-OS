"""launch-runbook — controls deploys, versioning, infra security.

DoD (03_AGENT_SPECS.md): rollback plan documented before every deploy.

This agent NEVER deploys. It assembles the runbook (preflight checks pulled
from Shared Memory, rollback plan, versioning) and files a
`production_deploy` approval request — always gated per the Approval Gate
Matrix (08_GOVERNANCE_AND_SAFETY.md). The deploy happens only after the
Chairperson approves, and even then by a human or a future gated executor.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.approval_gate import ApprovalGate
from departments.base import DepartmentAgent

REPO_ROOT = Path(__file__).resolve().parents[2]


class LaunchRunbook(DepartmentAgent):
    department = "COO"
    name = "launch-runbook"
    action_type = "prepare_deploy_runbook"

    def _latest_seo_audit(self, site_name: str) -> dict[str, Any] | None:
        """Cross-department read via the Ledger only — never a CMO call."""
        for e in self.ledger.recent(100, department="CMO"):
            if e["action_type"] != "seo_scan":
                continue
            inputs = json.loads(e["inputs"])
            if site_name in str(inputs.get("site", "")):
                outputs = json.loads(e["outputs"])
                return {"status": e["status"],
                        "issues": len(outputs.get("result", {}).get("issues", [])),
                        "ledger_id": e["id"]}
        return None

    def execute(self, task: dict[str, Any], task_id: str) -> dict[str, Any]:
        product = task.get("product", "")
        prop = task.get("property", {})
        root = REPO_ROOT / prop.get("root", "") if prop.get("root") else None

        audit = self._latest_seo_audit(product)
        preflight = [
            {"check": "site files exist",
             "ok": bool(root and root.is_dir()),
             "detail": str(root)},
            {"check": "latest SEO audit clean (CMO QA gate, via Ledger)",
             "ok": bool(audit and audit["status"] == "success"
                        and audit["issues"] == 0),
             "detail": audit or "no SEO audit found in Ledger for this product"},
            {"check": "domain purchased",
             "ok": bool(prop.get("domain")),
             "detail": prop.get("domain") or
                       "no domain — purchase is real spend, Chairperson decision"},
            {"check": "hosting configured",
             "ok": bool(prop.get("hosting")) and "planned" not in str(prop.get("hosting", "")),
             "detail": prop.get("hosting") or "none"},
            {"check": "repo under git (required for GitHub Pages)",
             "ok": (REPO_ROOT / ".git").is_dir(),
             "detail": "git init + remote needed before Pages deploy"},
        ]
        blockers = [c for c in preflight if not c["ok"]]

        rollback_plan = {
            "strategy": "static-site artifact rollback",
            "steps": [
                "Keep the previously deployed artifact (git tag / Pages "
                "deployment) untouched until the new deploy is verified",
                "Verify new deploy with a post-deploy crawl (site_inventory "
                "over the live URL set)",
                "On failure: re-publish the previous tagged artifact",
                "Log the rollback to the Ledger with the incident reference",
            ],
        }

        approval_id = None
        if task.get("request_deploy_approval", True):
            approval_id = ApprovalGate(self.ledger).request(
                "production_deploy",
                f"deploy {product}: first production deploy — "
                f"{len(blockers)} open blocker(s)",
                self.department, self.agent_id,
            )

        return {
            "runbook": {
                "product": product,
                "preflight": preflight,
                "rollback_plan": rollback_plan,
                "versioning": {"scheme": "git tag per deploy",
                               "next": f"{product}-v1"},
            },
            "blockers": blockers,
            "approval_id": approval_id,
            "requires_approval": bool(approval_id),
            "approval_reason": "production deploys are always gated "
                               "(08_GOVERNANCE_AND_SAFETY.md)",
        }

    def check_dod(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        notes = []
        rb = result.get("runbook", {})
        if not rb.get("rollback_plan", {}).get("steps"):
            notes.append("DoD fail: no rollback plan — nothing deploys without one")
        if not rb.get("preflight"):
            notes.append("DoD fail: no preflight checklist")
        if result.get("requires_approval"):
            notes.append(
                f"HALTED for Chairperson: {result.get('approval_reason')} — "
                f"{len(result.get('blockers', []))} open blocker(s), approval "
                f"{result.get('approval_id')}"
            )
        if not any(n.startswith("DoD fail") for n in notes):
            notes.append("DoD pass: rollback plan + preflight documented "
                         "before any deploy")
        return (not any(n.startswith("DoD fail") for n in notes), notes)
