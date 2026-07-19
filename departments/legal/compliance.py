"""compliance — cross-border regulatory checks (Legal Desk).

DoD (03_AGENT_SPECS.md): jurisdiction-specific checklist completed.

Monetization review: for each candidate revenue channel, produce a
requirements checklist with severity, met/unmet status derived from the
ACTUAL site files and property config (never assumed), and a source to
verify. Deterministic rule data, zero tokens.

Hard rules (08_GOVERNANCE_AND_SAFETY.md):
  - This desk prepares and flags; it never signs. Program signups are
    contracts -> Chairperson, always.
  - Program terms change; every source below must be re-verified at signup
    time. This agent states that explicitly rather than pretending its rule
    data is current law.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from departments.base import DepartmentAgent

REPO_ROOT = Path(__file__).resolve().parents[2]

SEV_BLOCKER, SEV_HIGH, SEV_INFO = "blocker", "high", "info"


class Compliance(DepartmentAgent):
    department = "LEGAL"
    name = "compliance"
    action_type = "monetization_compliance_review"

    # ---- site-state probes (facts, not opinions) ----

    def _site_state(self, site_root: Path) -> dict[str, Any]:
        pages = list(site_root.rglob("*.html")) if site_root.is_dir() else []
        text = " ".join(p.read_text(encoding="utf-8", errors="replace").lower()
                        for p in pages)
        return {
            "page_count": len(pages),
            "has_privacy_policy": any("privacy" in p.name.lower() for p in pages),
            # Must match actual disclosure phrasing — the mere word
            # "affiliate" appears in unrelated copy and is not a disclosure.
            "has_affiliate_disclosure": bool(re.search(
                r"qualifying purchases|earns? (a )?commission|"
                r"affiliate disclosure", text)),
            "uses_cookies_or_analytics": bool(
                re.search(r"gtag\(|analytics\.js|googletagmanager|_paq|cookie",
                          text)),
        }

    # ---- the review ----

    def execute(self, task: dict[str, Any], task_id: str) -> dict[str, Any]:
        prop = task.get("property", {})
        site_root = REPO_ROOT / prop.get("root", "")
        state = self._site_state(site_root)
        custom_domain = bool(prop.get("domain"))

        def req(item, severity, met, source, note=""):
            return {"item": item, "severity": severity, "met": met,
                    "source": source, "note": note}

        options = []

        # 1. Amazon Associates (or comparable affiliate program)
        amazon_reqs = [
            req("Privacy policy page on the site", SEV_HIGH,
                state["has_privacy_policy"],
                "https://affiliate-program.amazon.com/help/operating/policies",
                "required by program policies; also FTC/consumer-law hygiene"),
            req("Clear affiliate disclosure on every page with affiliate "
                "links, before/near the links", SEV_HIGH,
                state["has_affiliate_disclosure"],
                "https://www.ftc.gov/business-guidance (Endorsement Guides)",
                "FTC: disclosure must be clear and conspicuous"),
            req("Amazon's exact required identification statement", SEV_HIGH,
                False,
                "https://affiliate-program.amazon.com/help/operating/agreement",
                "verify current mandatory wording at signup — it changes"),
            req("Chairperson accepts the Operating Agreement", SEV_BLOCKER,
                False, "docs/08_GOVERNANCE_AND_SAFETY.md",
                "contract signature — always gated, never autonomous"),
            req("Content depth for program quality review", SEV_INFO,
                state["page_count"] >= 8,
                "https://affiliate-program.amazon.com/help",
                f"site has {state['page_count']} pages; more is safer"),
        ]
        options.append({
            "option": "affiliate (Amazon Associates or comparable)",
            "viability": "needs_prereqs",
            "requirements": amazon_reqs,
            "note": "Works on a github.io subdomain; custom domain preferred "
                    "but not required. Best first channel for a review site.",
        })

        # 2. Display ads (AdSense-class)
        options.append({
            "option": "display ads (AdSense-class)",
            "viability": "blocked" if not custom_domain else "needs_prereqs",
            "requirements": [
                req("Own custom domain", SEV_BLOCKER, custom_domain,
                    "https://support.google.com/adsense",
                    "github.io subdomains are not eligible for AdSense; "
                    "verify current policy"),
                req("Privacy policy + cookie/consent handling (GDPR/ePrivacy "
                    "for EU visitors)", SEV_HIGH,
                    state["has_privacy_policy"] and not state["uses_cookies_or_analytics"],
                    "https://support.google.com/adsense (+ GDPR)",
                    "ad tags set cookies; consent management required"),
            ],
            "note": "Deferred until a custom domain exists (real spend — "
                    "Chairperson decision).",
        })

        # 3. Sponsored content
        options.append({
            "option": "sponsored content",
            "viability": "premature",
            "requirements": [
                req("Per-post FTC disclosure", SEV_HIGH, False,
                    "https://www.ftc.gov/business-guidance"),
                req("Chairperson signs each sponsorship contract", SEV_BLOCKER,
                    False, "docs/08_GOVERNANCE_AND_SAFETY.md"),
            ],
            "note": "No traffic yet — nothing to sell sponsors. Revisit with "
                    "Search Console data.",
        })

        # Site instrumentation (prerequisite for measuring any revenue)
        options.append({
            "option": "analytics instrumentation",
            "viability": "needs_prereqs",
            "requirements": [
                req("Privacy policy before any on-site tracking", SEV_HIGH,
                    state["has_privacy_policy"], "GDPR Art. 13 / general "
                    "consumer-privacy hygiene"),
                req("Prefer cookieless analytics to avoid consent-banner "
                    "burden", SEV_INFO, not state["uses_cookies_or_analytics"],
                    "GDPR/ePrivacy",
                    "site currently sets no cookies — keep it that way if "
                    "possible"),
            ],
            "note": "Search Console (already live) is server-side and needs "
                    "no on-site consent.",
        })

        jurisdiction = [
            {"item": "Affiliate/ad income is taxable income in the "
                     "Chairperson's jurisdiction (INR-based per config); "
                     "cross-border payouts (e.g., Amazon US) may involve "
                     "foreign-remittance reporting",
             "severity": SEV_HIGH,
             "action": "Chairperson consults a tax professional before first "
                       "payout — this desk flags, it does not give tax advice"},
            {"item": "Static site currently sets no cookies and collects no "
                     "user data — GDPR exposure is minimal until "
                     "analytics/ads are added",
             "severity": SEV_INFO, "action": "re-review when instrumenting"},
        ]

        unmet_blockers = [r["item"] for o in options
                          for r in o["requirements"]
                          if r["severity"] == SEV_BLOCKER and not r["met"]]
        return {
            "property": prop.get("name"),
            "site_state": state,
            "options": options,
            "jurisdiction_checklist": jurisdiction,
            "unmet_blockers": unmet_blockers,
            "recommendation": (
                "Sequence: (1) add privacy policy + affiliate-disclosure "
                "pages (autonomous content work), (2) Chairperson decides on "
                "Amazon Associates signup (contract gate), (3) defer ads "
                "until custom domain, (4) keep the site cookieless."),
            "verify_note": "All program terms must be re-verified at signup; "
                           "rule data here is a checklist, not current law.",
        }

    def check_dod(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        notes = []
        if not result.get("options"):
            notes.append("DoD fail: no monetization options reviewed")
        for o in result.get("options", []):
            if not o.get("requirements"):
                notes.append(f"DoD fail: option '{o.get('option')}' has no "
                             "requirements checklist")
            for r in o.get("requirements", []):
                if not r.get("source") or r.get("severity") not in (
                        SEV_BLOCKER, SEV_HIGH, SEV_INFO):
                    notes.append(f"DoD fail: unsourced/unranked requirement "
                                 f"in '{o.get('option')}'")
        if not result.get("jurisdiction_checklist"):
            notes.append("DoD fail: jurisdiction checklist missing")
        if not notes:
            notes.append(
                f"DoD pass: {len(result['options'])} options reviewed, every "
                f"requirement sourced+ranked, jurisdiction checklist done, "
                f"{len(result['unmet_blockers'])} unmet blocker(s) flagged")
        return (not any(n.startswith("DoD fail") for n in notes), notes)
