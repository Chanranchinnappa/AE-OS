"""Shared truthfulness QA for CMO content agents.

Used by programmatic-seo and ai-seo (and any future content agent). Two
deterministic gates, zero tokens:

  1. Seller voice — this venture runs independent guide sites; generated
     content may never speak as a manufacturer ("we've developed", "our
     range").
  2. Unsourced numeric claims — any number with a unit (years, hours, %,
     mAh, lumens...) must appear in the provided source material, or it is
     treated as fabricated.

Plus a scrubber for LLM meta-commentary ("Here is the page:", "Note: I
avoided saying 'we'"), which is not content and must not reach QA or a page.
"""
from __future__ import annotations

import re

SELLER_VOICE = re.compile(r"\b(we|we've|we're|our|us)\b", re.IGNORECASE)
NUMERIC_CLAIM = re.compile(
    r"\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?\s*"
    r"(?:%|percent|years?|hours?|months?|days?|mah|lumens?|watts?)\b",
    re.IGNORECASE,
)
META_LINE = re.compile(
    r"^\s*(note:|here is|here's|i've |i have |as requested|hope this|"
    r"let me know)", re.IGNORECASE)


def scrub_meta(text: str) -> str:
    """Drop meta-commentary lines; return the actual content."""
    return "\n".join(l for l in text.splitlines()
                     if not META_LINE.match(l)).strip()


def content_violations(text: str, allowed_source_text: str = "") -> list[str]:
    """Return truthfulness violations in `text` (empty list = clean).

    `allowed_source_text` is any string containing the numbers the content is
    allowed to state (a JSON dump of the source row / source facts works).
    """
    violations = []
    m = SELLER_VOICE.search(text)
    if m:
        violations.append(
            f"seller-voice claim ('{m.group()}...') — independent guide "
            "sites never speak as the manufacturer"
        )
    allowed = set(re.findall(r"\d+(?:\.\d+)?", allowed_source_text))
    for claim in NUMERIC_CLAIM.finditer(text):
        nums = re.findall(r"\d+(?:\.\d+)?", claim.group())
        if any(n not in allowed for n in nums):
            violations.append(f"unsourced numeric claim: '{claim.group().strip()}'")
    return violations
