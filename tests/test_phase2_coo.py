"""Phase 2 — COO department (sop-builder, launch-runbook) + CEO integration.

Run: python -m unittest tests.test_phase2_coo -v
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

from core import kill_switch
from core.approval_gate import ApprovalGate
from core.ceo import CEO
from core.model_router import ModelRouter, RouterConfig
from departments.coo import LaunchRunbook, SopBuilder
from memory import db as _db
from memory.ledger import Ledger


def fresh():
    conn = _db.connect(":memory:")
    ledger = Ledger(conn)
    router = ModelRouter(ledger, RouterConfig())
    return ledger, router


class TestSopBuilder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ledger, self.router = fresh()
        self.agent = SopBuilder(self.ledger, self.router, sops_dir=self.tmp)

    def _seed_entry(self) -> str:
        return self.ledger.log("CMO", "cmo.seo-audit", "seo_scan", "success")

    def test_sop_written_versioned_and_linked(self):
        src = self._seed_entry()
        out = self.agent.run({
            "title": "Publish a content property",
            "steps": ["Run seo-audit", "Fix issues", "Re-audit until clean"],
            "source_ledger_ids": [src],
        })
        self.assertEqual(out["status"], "success")
        self.assertEqual(out["result"]["version"], 1)
        text = Path(out["result"]["file"]).read_text()
        self.assertIn(src, text)
        self.assertIn("1. Run seo-audit", text)

    def test_version_bumps_on_recodify(self):
        src = self._seed_entry()
        task = {"title": "Publish a content property",
                "steps": ["Run seo-audit"], "source_ledger_ids": [src]}
        self.agent.run(task)
        out = self.agent.run(task)
        self.assertEqual(out["result"]["version"], 2)

    def test_no_provenance_fails(self):
        out = self.agent.run({"title": "Vibes-based process",
                              "steps": ["Do things"], "source_ledger_ids": []})
        self.assertEqual(out["status"], "failed")

    def test_unknown_ledger_id_fails(self):
        out = self.agent.run({"title": "T", "steps": ["s"],
                              "source_ledger_ids": ["not-a-real-id"]})
        self.assertEqual(out["status"], "failed")
        self.assertTrue(any("unknown Ledger ids" in n.lower() or
                            "unknown ledger ids" in n.lower()
                            for n in out["dod_notes"]))


class TestLaunchRunbook(unittest.TestCase):
    def test_always_halts_for_approval_with_rollback_documented(self):
        ledger, router = fresh()
        out = LaunchRunbook(ledger, router).run({
            "product": "brightpaths",
            "property": {"name": "brightpaths", "root": "sites/brightpaths",
                         "domain": None, "hosting": "github_pages (planned)",
                         "status": "in_build"},
        })
        self.assertEqual(out["status"], "needs_approval")
        rb = out["result"]["runbook"]
        self.assertTrue(rb["rollback_plan"]["steps"])
        self.assertTrue(rb["preflight"])
        # blockers honestly reported: no domain, hosting planned-only, no git
        blocker_checks = {b["check"] for b in out["result"]["blockers"]}
        self.assertIn("domain purchased", blocker_checks)
        # approval filed and pending for the Chairperson
        gate = ApprovalGate(ledger)
        self.assertEqual(gate.status(out["result"]["approval_id"]), "pending")

    def test_missing_rollback_fails_dod(self):
        ledger, router = fresh()
        agent = LaunchRunbook(ledger, router)
        ok, notes = agent.check_dod({"runbook": {"preflight": [{"check": "x"}],
                                                 "rollback_plan": {}}})
        self.assertFalse(ok)
        self.assertTrue(any("rollback" in n for n in notes))

    def test_clean_audit_recognized_from_ledger(self):
        ledger, router = fresh()
        ledger.log("CMO", "cmo.seo-audit", "seo_scan", "success",
                   inputs={"site": "brightpaths (re-audit)"},
                   outputs={"result": {"issues": []}})
        agent = LaunchRunbook(ledger, router)
        audit = agent._latest_seo_audit("brightpaths")
        self.assertIsNotNone(audit)
        self.assertEqual(audit["issues"], 0)


class TestCEOAllocatesCOO(unittest.TestCase):
    def tearDown(self):
        kill_switch.resume()

    def test_cycle_prepares_runbook_and_halts_without_duplicates(self):
        ledger, router = fresh()
        ceo = CEO(ledger, router)
        out1 = ceo.run_cycle()
        by_agent = {r["agent_id"]: r for r in out1["results"]}
        self.assertIn("coo.launch-runbook", by_agent)
        self.assertEqual(by_agent["coo.launch-runbook"]["status"],
                         "needs_approval")
        self.assertIn("pending approval", out1["brief"])
        # second cycle: pending deploy approval -> COO not re-allocated
        out2 = ceo.run_cycle()
        agents2 = [r["agent_id"] for r in out2["results"]]
        self.assertNotIn("coo.launch-runbook", agents2)
        self.assertEqual(len(ApprovalGate(ledger).pending()), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
