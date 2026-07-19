"""Phase 3 — Legal Desk pilot: compliance monetization review.

Run: python -m unittest tests.test_phase3_legal -v
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("AE_OS_PAUSE_FILE",
                      os.path.join(tempfile.mkdtemp(), "GLOBAL_PAUSE"))

from core.model_router import ModelRouter, RouterConfig
from departments.legal import Compliance
from memory import db as _db
from memory.ledger import Ledger

BRIGHTPATHS = {"name": "brightpaths", "root": "sites/brightpaths",
               "domain": None, "status": "live"}


def make():
    ledger = Ledger(_db.connect(":memory:"))
    return ledger, Compliance(ledger, ModelRouter(ledger, RouterConfig()))


class TestComplianceReview(unittest.TestCase):
    def test_review_completes_and_logs(self):
        ledger, agent = make()
        out = agent.run({"property": BRIGHTPATHS})
        self.assertEqual(out["status"], "success")
        entry = ledger.recent(1)[0]
        self.assertEqual(entry["agent_id"], "legal.compliance")
        self.assertEqual(entry["action_type"],
                         "monetization_compliance_review")

    def test_every_requirement_sourced_and_ranked(self):
        _, agent = make()
        out = agent.run({"property": BRIGHTPATHS})
        for o in out["result"]["options"]:
            self.assertTrue(o["requirements"], o["option"])
            for r in o["requirements"]:
                self.assertTrue(r["source"])
                self.assertIn(r["severity"], ("blocker", "high", "info"))

    def test_site_facts_derived_not_assumed(self):
        _, agent = make()
        out = agent.run({"property": BRIGHTPATHS})
        state = out["result"]["site_state"]
        # real brightpaths today: no privacy policy, no cookies/analytics
        self.assertFalse(state["has_privacy_policy"])
        self.assertFalse(state["uses_cookies_or_analytics"])
        self.assertGreaterEqual(state["page_count"], 8)

    def test_adsense_blocked_without_domain(self):
        _, agent = make()
        out = agent.run({"property": BRIGHTPATHS})
        ads = next(o for o in out["result"]["options"]
                   if o["option"].startswith("display ads"))
        self.assertEqual(ads["viability"], "blocked")

    def test_contract_signature_always_flagged_as_blocker(self):
        _, agent = make()
        out = agent.run({"property": BRIGHTPATHS})
        self.assertTrue(any("Operating Agreement" in b
                            for b in out["result"]["unmet_blockers"]))

    def test_jurisdiction_checklist_required_by_dod(self):
        _, agent = make()
        result = agent.execute({"property": BRIGHTPATHS}, "t1")
        result["jurisdiction_checklist"] = []
        ok, notes = agent.check_dod(result)
        self.assertFalse(ok)
        self.assertTrue(any("jurisdiction" in n for n in notes))


if __name__ == "__main__":
    unittest.main(verbosity=2)
