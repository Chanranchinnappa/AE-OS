"""mktg-psychology — behavioral trigger analysis for messaging.

DoD (03_AGENT_SPECS.md): recommendation backed by data, not just theory.
Every recommendation must reference a concrete data point from the provided
funnel/audience data; zero data in means zero recommendations out.
"""
from __future__ import annotations

from typing import Any

from .base import CMOAgent

# behavioral trigger -> the funnel signal that justifies deploying it
_TRIGGER_MAP = (
    ("loss_aversion", lambda s: s.get("drop_off_pct", 0) >= 40,
     "high drop-off suggests visitors don't fear missing out on anything yet"),
    ("social_proof", lambda s: s.get("bounce_pct", 0) >= 50,
     "high bounce suggests trust is not established fast enough"),
    ("commitment_consistency", lambda s: s.get("repeat_visit_pct", 0) >= 20,
     "returning visitors respond to small-ask escalation"),
)


class MktgPsychology(CMOAgent):
    name = "mktg-psychology"
    action_type = "behavioral_analysis"

    def execute(self, task: dict[str, Any], task_id: str) -> dict[str, Any]:
        stages = task.get("funnel_data", [])
        audience = task.get("audience", "")
        recommendations = []
        for stage in stages:
            for trigger, applies, rationale in _TRIGGER_MAP:
                if applies(stage):
                    copy_idea = self.draft(
                        f"Suggest one message for audience '{audience}' at funnel "
                        f"stage '{stage.get('stage')}' using the {trigger} trigger. "
                        f"Justification: {rationale}.",
                        task_id,
                    )
                    recommendations.append({
                        "trigger": trigger,
                        "recommendation": copy_idea,
                        "evidence": {
                            "stage": stage.get("stage"),
                            "metrics": {k: v for k, v in stage.items() if k != "stage"},
                            "rationale": rationale,
                        },
                    })
        return {"audience": audience, "stages_analyzed": len(stages),
                "recommendations": recommendations}

    def check_dod(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        notes = []
        if result.get("stages_analyzed", 0) == 0:
            notes.append(
                "DoD fail: no funnel data provided — recommendations would be "
                "pure theory, which the DoD forbids"
            )
        for rec in result.get("recommendations", []):
            ev = rec.get("evidence", {})
            if not ev.get("stage") or not ev.get("metrics"):
                notes.append(
                    f"DoD fail: recommendation '{rec.get('trigger')}' lacks a "
                    "concrete data point"
                )
        if not notes:
            notes.append("DoD pass: all recommendations tied to observed funnel data")
        return (not any(n.startswith("DoD fail") for n in notes), notes)
