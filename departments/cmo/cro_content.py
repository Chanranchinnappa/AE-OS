"""cro-content — funnel-facing on-page conversion tests (distinct from CRO dept).

DoD (03_AGENT_SPECS.md): test has control, variant, sample-size check.
"""
from __future__ import annotations

import math
from typing import Any

from .base import CMOAgent


def sample_size_per_arm(baseline_rate: float, mde_abs: float) -> int:
    """Rule-of-thumb two-arm test size: n = 16 * p(1-p) / delta^2."""
    if not (0 < baseline_rate < 1) or mde_abs <= 0:
        return 0
    return math.ceil(16 * baseline_rate * (1 - baseline_rate) / (mde_abs ** 2))


class CroContent(CMOAgent):
    name = "cro-content"
    action_type = "conversion_test_design"

    def execute(self, task: dict[str, Any], task_id: str) -> dict[str, Any]:
        page = task.get("page", "")
        hypothesis = task.get("hypothesis", "")
        baseline = task.get("baseline_conversion_rate", 0.0)
        mde = task.get("min_detectable_effect", 0.0)
        visitors = task.get("baseline_visitors_per_day", 0)

        n = sample_size_per_arm(baseline, mde)
        duration = math.ceil(2 * n / visitors) if visitors > 0 and n > 0 else None

        variant_copy = self.draft(
            f"Rewrite the element under test on {page} to test this hypothesis: "
            f"{hypothesis}. Return only the variant copy.",
            task_id,
        )
        return {
            "page": page,
            "hypothesis": hypothesis,
            "control": {"description": f"current live version of {page}"},
            "variant": {"description": hypothesis, "copy": variant_copy},
            "sample_size_check": {
                "baseline_conversion_rate": baseline,
                "min_detectable_effect": mde,
                "required_per_arm": n,
                "estimated_duration_days": duration,
                "feasible": bool(n and duration and duration <= 45),
            },
        }

    def check_dod(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        notes = []
        if not result.get("control"):
            notes.append("DoD fail: no control defined")
        if not result.get("variant", {}).get("copy"):
            notes.append("DoD fail: no variant produced")
        ssc = result.get("sample_size_check", {})
        if not ssc.get("required_per_arm"):
            notes.append(
                "DoD fail: sample-size check missing or invalid "
                "(need baseline rate in (0,1) and a positive min detectable effect)"
            )
        elif not ssc.get("feasible"):
            notes.append(
                "DoD fail: test infeasible — would run "
                f"{ssc.get('estimated_duration_days', '???')} days at current traffic"
            )
        if not notes:
            notes.append("DoD pass: control + variant + feasible sample-size check")
        return (not any(n.startswith("DoD fail") for n in notes), notes)
