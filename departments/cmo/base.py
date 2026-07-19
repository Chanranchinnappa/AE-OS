"""Base class for every CMO sub-agent.

Generic agent contract (guard -> execute -> DoD -> Ledger) lives in
`departments.base.DepartmentAgent`. This subclass adds what is specific to
CMO content work: the gated drafting loop backed by the shared truthfulness
QA in `qa.py`.
"""
from __future__ import annotations

from departments.base import DepartmentAgent

DEPARTMENT = "CMO"


class CMOAgent(DepartmentAgent):
    department = DEPARTMENT

    def draft_gated(self, prompt: str, task_id: str, qa_fn,
                    max_attempts: int = 3) -> tuple[str, list[str], int]:
        """Draft with a QA gate: scrub meta-commentary, QA, retry with the
        violations fed back into the prompt. Each rejected attempt is recorded
        as a Tier 0 quality failure so the router can authorize escalation
        once a Tier 1 provider is wired.

        Returns (text, remaining_failures, attempts_used); failures is empty
        on success.
        """
        from . import qa as _qa
        text, failures = "", []
        for attempt in range(1, max_attempts + 1):
            text = _qa.scrub_meta(self.draft(prompt, task_id))
            failures = qa_fn(text)
            if not failures:
                return text, [], attempt
            self.router.record_failure(task_id, 0)
            prompt += ("\n\nYour previous draft was REJECTED for: "
                       + "; ".join(failures)
                       + ". Rewrite the full text fixing every violation.")
        return text, failures, max_attempts
