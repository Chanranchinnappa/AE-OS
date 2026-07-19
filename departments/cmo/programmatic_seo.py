"""programmatic-seo — mass-builds data-driven landing pages.

DoD (03_AGENT_SPECS.md): pages pass QA, indexed check scheduled. QA includes
the shared truthfulness gate (qa.py): no seller-voice, no numeric claims
absent from the source data row. A fluent page with a fabricated claim is a
failed page, not a shipped one.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from . import qa
from .base import CMOAgent

INDEX_CHECK_DELAY_DAYS = 7
MIN_BODY_CHARS = 40  # dry-run floor; raise for live content
MAX_DRAFT_ATTEMPTS = 3


class ProgrammaticSeo(CMOAgent):
    name = "programmatic-seo"
    action_type = "build_landing_pages"

    @staticmethod
    def _scrub(text: str) -> str:
        return qa.scrub_meta(text)

    def _qa(self, page: dict[str, Any]) -> list[str]:
        failures = []
        if not page.get("title"):
            failures.append("empty title")
        body = page.get("body") or ""
        if len(body) < MIN_BODY_CHARS:
            failures.append(f"body under {MIN_BODY_CHARS} chars")
        kw = page.get("keyword", "")
        if kw and kw.lower() not in (page.get("title", "") + body).lower():
            failures.append("keyword absent from title and body")
        failures.extend(qa.content_violations(
            body, json.dumps(page.get("source_row", {}))))
        return failures

    def execute(self, task: dict[str, Any], task_id: str) -> dict[str, Any]:
        template = task.get("template", "")
        dataset = task.get("dataset", [])
        base_rules = (
            "HARD RULES (output is machine-rejected if violated):\n"
            "1. NEVER use the words 'we', 'our', or 'us' — this site reviews "
            "products, it does not make or sell them. Address the reader as "
            "'you'.\n"
            "2. NEVER state a number (hours, years, %, lumens) that is not in "
            "the data above.\n"
            "3. Output ONLY the page body — no preamble, no notes about how "
            "you followed these rules.\n"
            "4. Plain informative prose only — no invented brand, product "
            "line, or guarantee."
        )
        pages = []
        for row in dataset:
            keyword = row.get("keyword", "")
            title = (template.split("|")[0].strip().format(**row)
                     if template else "")

            def page_qa(body: str, _title=title, _kw=keyword, _row=row) -> list[str]:
                return self._qa({"title": _title, "keyword": _kw,
                                 "body": body, "source_row": _row})

            body, failures, attempts = self.draft_gated(
                f"Write the body copy for an INDEPENDENT buyer's-guide landing "
                f"page targeting the keyword '{keyword}', using ONLY this "
                f"data: {row}. Template: {template}\n{base_rules}",
                task_id, page_qa, MAX_DRAFT_ATTEMPTS,
            )
            pages.append({
                "url_slug": keyword.lower().replace(" ", "-") if keyword else "",
                "keyword": keyword,
                "title": title,
                "body": body,
                "source_row": row,
                "attempts": attempts,
                "qa_passed": not failures,
                "qa_failures": failures,
            })

        check_date = (datetime.now(timezone.utc)
                      + timedelta(days=INDEX_CHECK_DELAY_DAYS)).date().isoformat()
        return {
            "pages": pages,
            "index_check": {"scheduled_for": check_date,
                            "urls": [p["url_slug"] for p in pages if p["qa_passed"]]},
        }

    def check_dod(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        notes = []
        pages = result.get("pages", [])
        if not pages:
            notes.append("DoD fail: no pages built")
        for p in pages:
            if not p.get("qa_passed"):
                notes.append(
                    f"DoD fail: page '{p.get('url_slug') or '?'}' failed QA: "
                    f"{', '.join(p.get('qa_failures', []))}"
                )
        if not result.get("index_check", {}).get("scheduled_for"):
            notes.append("DoD fail: indexed check not scheduled")
        if not notes:
            notes.append("DoD pass: all pages passed QA, index check scheduled")
        return (not any(n.startswith("DoD fail") for n in notes), notes)
