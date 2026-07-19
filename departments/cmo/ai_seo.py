"""ai-seo — optimizes content to rank in AI engine summaries.

DoD (03_AGENT_SPECS.md): content cites real sources, no hallucinated claims.
Citation discipline per 09_TRILLION_INTEGRATION.md Concept 6: every claim maps
to a source that was actually provided — a citation not in the input source
list is treated as hallucinated and fails the DoD.

The drafted prose itself also passes the shared truthfulness gate (qa.py):
no seller voice, and no numeric claims that are absent from the provided
source facts.
"""
from __future__ import annotations

import json
from typing import Any

from . import qa
from .base import CMOAgent


class AiSeo(CMOAgent):
    name = "ai-seo"
    action_type = "ai_engine_optimization"

    def execute(self, task: dict[str, Any], task_id: str) -> dict[str, Any]:
        brief = task.get("content_brief", "")
        sources = task.get("sources", [])
        # Claims are built strictly from provided sources — one per source in
        # dry-run; a live Tier-0 model gets the same hard constraint in-prompt.
        claims = [{"claim": f"Key fact drawn from {s.get('url')}: {s.get('fact', '')}",
                   "source": s.get("url")}
                  for s in sources]

        source_text = json.dumps(sources)
        draft, violations, attempts = self.draft_gated(
            f"Write an answer-engine-optimized section for brief '{brief}'. "
            f"Use ONLY these sourced facts: {claims}. "
            "Structure: direct answer first, then supporting cited facts.\n"
            "HARD RULES (output is machine-rejected if violated):\n"
            "1. NEVER use the words 'we', 'our', or 'us' — write as an "
            "independent guide.\n"
            "2. NEVER state a number that is not in the sourced facts above.\n"
            "3. Output ONLY the content section — no preamble or notes.",
            task_id,
            lambda text: qa.content_violations(text, source_text),
        )
        return {
            "brief": brief,
            "draft": draft,
            "draft_attempts": attempts,
            "content_violations": violations,
            "claims": claims,
            "citations": sorted({c["source"] for c in claims if c["source"]}),
            "allowed_sources": [s.get("url") for s in sources],
        }

    def check_dod(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        notes = []
        allowed = set(result.get("allowed_sources", []))
        claims = result.get("claims", [])
        if not result.get("citations"):
            notes.append("DoD fail: no citations — uncited AI-SEO content never ships")
        for c in claims:
            if not c.get("source"):
                notes.append(f"DoD fail: uncited claim: {c.get('claim', '?')[:60]}")
            elif c["source"] not in allowed:
                notes.append(
                    f"DoD fail: hallucinated citation {c['source']} "
                    "(not in provided source list)"
                )
        for v in result.get("content_violations", []):
            notes.append(f"DoD fail: truthfulness gate: {v}")
        if not notes:
            notes.append("DoD pass: every claim cites a real provided source; "
                         "draft passed the truthfulness gate")
        return (not any(n.startswith("DoD fail") for n in notes), notes)
