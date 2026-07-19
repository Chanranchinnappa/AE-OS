"""ad-creative — scales ad graphic/text variants.

DoD (03_AGENT_SPECS.md): each variant tagged with the hypothesis being tested.

Money gate (08_GOVERNANCE_AND_SAFETY.md): creative generation is autonomous,
but any requested spend above the configured daily marketing ceiling makes the
whole action `needs_approval` — it halts for the Chairperson, never auto-runs.
Bootstrap ceiling is 0, so ANY live spend request halts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import CMOAgent

_SETTINGS = Path(__file__).resolve().parents[2] / "config" / "settings.json"


def daily_spend_ceiling() -> float:
    if _SETTINGS.exists():
        cfg = json.loads(_SETTINGS.read_text())
        return float(cfg.get("budget_ceilings", {}).get("daily_marketing_spend", 0))
    return 0.0


class AdCreative(CMOAgent):
    name = "ad-creative"
    action_type = "generate_ad_variants"

    def execute(self, task: dict[str, Any], task_id: str) -> dict[str, Any]:
        product = task.get("product", "")
        hypotheses = task.get("hypotheses", [])
        requested_spend = float(task.get("requested_daily_spend", 0.0))

        variants = []
        for i, hyp in enumerate(hypotheses):
            copy = self.draft(
                f"Write one short ad (headline + body <=90 chars) for {product} "
                f"testing this hypothesis: {hyp}",
                task_id,
            )
            variants.append({"variant_id": f"{task_id[:8]}-v{i}",
                             "hypothesis": hyp, "copy": copy})

        ceiling = daily_spend_ceiling()
        result: dict[str, Any] = {
            "product": product,
            "variants": variants,
            "requested_daily_spend": requested_spend,
            "daily_spend_ceiling": ceiling,
        }
        if requested_spend > ceiling:
            result["requires_approval"] = True
            result["approval_reason"] = (
                f"Requested daily ad spend {requested_spend} exceeds ceiling "
                f"{ceiling} (config/settings.json). Halted for Chairperson."
            )
        return result

    def check_dod(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        notes = []
        variants = result.get("variants", [])
        if not variants:
            notes.append("DoD fail: no variants generated")
        for v in variants:
            if not v.get("hypothesis"):
                notes.append(f"DoD fail: variant {v.get('variant_id')} has no hypothesis tag")
        if result.get("requires_approval"):
            notes.append(f"HALTED: {result.get('approval_reason')}")
        if not any(n.startswith("DoD fail") for n in notes):
            notes.append("DoD pass: every variant tagged with its hypothesis")
        return (not any(n.startswith("DoD fail") for n in notes), notes)
