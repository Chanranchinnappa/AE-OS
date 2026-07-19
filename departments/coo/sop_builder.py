"""sop-builder — codifies repeatable actions into SOPs.

DoD (03_AGENT_SPECS.md): SOP versioned, linked to originating logs.

Every SOP must cite the Ledger entries it was distilled from — an SOP with
no provenance is an opinion, not a procedure. Deterministic, zero tokens.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from departments.base import DepartmentAgent
from memory.registry import Registry

REPO_ROOT = Path(__file__).resolve().parents[2]


class SopBuilder(DepartmentAgent):
    department = "COO"
    name = "sop-builder"
    action_type = "codify_sop"

    def __init__(self, ledger=None, router=None, sops_dir: Path | str | None = None):
        super().__init__(ledger, router)
        self.sops_dir = Path(sops_dir) if sops_dir else REPO_ROOT / "docs" / "sops"

    def _valid_ledger_ids(self, ids: list[str]) -> set[str]:
        if not ids:
            return set()
        marks = ",".join("?" * len(ids))
        rows = self.ledger.conn.execute(
            f"SELECT id FROM ledger WHERE id IN ({marks})", ids).fetchall()
        return {r["id"] for r in rows}

    def execute(self, task: dict[str, Any], task_id: str) -> dict[str, Any]:
        title = task.get("title", "")
        steps = task.get("steps", [])
        source_ids = task.get("source_ledger_ids", [])
        valid_ids = self._valid_ledger_ids(source_ids)

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "untitled"
        registry = Registry(self.ledger.conn, self.ledger)
        index = registry.get("COO", "sops") or {}
        version = (index.get(slug) or {}).get("version", 0) + 1

        file_path = self.sops_dir / f"{slug}.md"
        if title and steps and valid_ids == set(source_ids) and source_ids:
            self.sops_dir.mkdir(parents=True, exist_ok=True)
            lines = [
                f"# SOP: {title}",
                "",
                f"- **Version**: {version}",
                f"- **Updated**: {datetime.now(timezone.utc).date().isoformat()}",
                f"- **Owner**: {self.agent_id}",
                "- **Originating Ledger entries**: "
                + ", ".join(f"`{i}`" for i in source_ids),
                "",
                "## Steps",
                "",
            ]
            lines += [f"{n}. {s}" for n, s in enumerate(steps, 1)]
            file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            index[slug] = {"version": version, "file": str(file_path),
                           "title": title}
            registry.set("COO", "sops", index, self.agent_id)
            written = True
        else:
            written = False

        return {
            "slug": slug, "title": title, "version": version,
            "file": str(file_path), "written": written,
            "steps_count": len(steps),
            "source_ledger_ids": source_ids,
            "invalid_source_ids": sorted(set(source_ids) - valid_ids),
        }

    def check_dod(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        notes = []
        if result.get("steps_count", 0) == 0:
            notes.append("DoD fail: SOP has no steps")
        if not result.get("source_ledger_ids"):
            notes.append("DoD fail: SOP not linked to any originating Ledger entry")
        if result.get("invalid_source_ids"):
            notes.append("DoD fail: unknown Ledger ids cited: "
                         f"{result['invalid_source_ids']}")
        if not result.get("written"):
            notes.append("DoD fail: SOP file not written")
        if not notes:
            notes.append(f"DoD pass: SOP '{result['slug']}' v{result['version']} "
                         "written, versioned, provenance linked")
        return (not any(n.startswith("DoD fail") for n in notes), notes)
