"""seo-audit — continuous on-page/technical SEO scans.

DoD (03_AGENT_SPECS.md): report with scored issues + fixes, logged to Ledger.

Checks are deterministic rules (no LLM needed to detect a missing meta tag —
11_TOKEN_OPTIMIZATION.md Rule 5: the cheapest token is the one never spent).
The router is used only to draft the human-readable summary.
"""
from __future__ import annotations

from typing import Any

from .base import CMOAgent

# (check function, issue label, severity 1-10, fix)
_RULES = (
    (lambda p: not p.get("title"), "missing title tag", 9,
     "Write a unique <=60-char title containing the primary keyword"),
    (lambda p: len(p.get("title") or "") > 60, "title too long (>60 chars)", 4,
     "Shorten title to <=60 chars, keyword first"),
    (lambda p: not p.get("meta_description"), "missing meta description", 7,
     "Add a 120-155 char meta description with a call to action"),
    (lambda p: not p.get("h1"), "missing H1", 8,
     "Add exactly one H1 matching search intent"),
    (lambda p: (p.get("word_count") or 0) < 300, "thin content (<300 words)", 6,
     "Expand to 800+ words of substantive, sourced content"),
    (lambda p: not p.get("internal_links"), "no internal links", 5,
     "Link to 2-3 related pages on the same property"),
)


class SeoAudit(CMOAgent):
    name = "seo-audit"
    action_type = "seo_scan"

    def execute(self, task: dict[str, Any], task_id: str) -> dict[str, Any]:
        site = task.get("site", "unknown-site")
        pages = task.get("pages", [])
        issues = []
        for page in pages:
            for check, label, severity, fix in _RULES:
                if check(page):
                    issues.append({
                        "page": page.get("url", "?"),
                        "issue": label,
                        "severity_score": severity,
                        "fix": fix,
                    })
        issues.sort(key=lambda i: -i["severity_score"])
        summary = self.draft(
            f"Summarize this SEO audit of {site} in 3 bullet points: "
            f"{len(pages)} pages scanned, {len(issues)} issues, "
            f"top issue: {issues[0]['issue'] if issues else 'none'}.",
            task_id,
        )
        return {"site": site, "pages_scanned": len(pages),
                "issues": issues, "summary": summary}

    def check_dod(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        notes = []
        if result.get("pages_scanned", 0) == 0:
            notes.append("DoD fail: no pages scanned — nothing audited")
        for issue in result.get("issues", []):
            if not isinstance(issue.get("severity_score"), int):
                notes.append(f"DoD fail: unscored issue on {issue.get('page')}")
            if not issue.get("fix"):
                notes.append(f"DoD fail: issue without a fix on {issue.get('page')}")
        if not notes:
            notes.append("DoD pass: every issue scored with a concrete fix")
        return (not any(n.startswith("DoD fail") for n in notes), notes)
