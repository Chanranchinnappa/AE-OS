"""Phase 2 verification — CEO orchestrator, Approval Gate Matrix, CFO pilot.

Covers the roadmap items (10_BUILD_ROADMAP.md Phase 2):
  - Approval Gate Matrix: gated actions actually halt, decisions are
    explicit, nothing auto-approves
  - CEO Operating Loop: ingest -> allocate -> dispatch -> compile
  - persona brief: <=200 words, ends with a recommended next action, never
    fabricates revenue
  - cross-department handoff via Shared Memory only (CFO reads CMO's Ledger
    entries; no direct calls)

Run: python -m unittest tests.test_phase2_ceo -v
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["AE_OS_PAUSE_FILE"] = os.path.join(tempfile.mkdtemp(), "GLOBAL_PAUSE")

from core import kill_switch
from core.approval_gate import (ALWAYS_GATED, ApprovalError, ApprovalGate,
                                request_spend, requires_approval)
from core.ceo import CEO
from core.model_router import ModelRouter, RouterConfig
from departments.cfo import PricingMath
from memory import db as _db
from memory.ledger import Ledger
from memory.registry import Registry


def fresh():
    conn = _db.connect(":memory:")
    ledger = Ledger(conn)
    router = ModelRouter(ledger, RouterConfig())  # dry_run tier 0
    return ledger, router


class TestApprovalMatrix(unittest.TestCase):
    def test_always_gated_actions(self):
        for action in ALWAYS_GATED:
            self.assertTrue(requires_approval(action))

    def test_spend_above_ceiling_gated(self):
        self.assertTrue(requires_approval("spend", amount=5.0))   # ceiling is 0

    def test_zero_spend_not_gated(self):
        self.assertFalse(requires_approval("spend", amount=0.0))

    def test_routine_action_not_gated(self):
        self.assertFalse(requires_approval("seo_scan"))


class TestApprovalGateWorkflow(unittest.TestCase):
    def test_request_halts_and_decision_is_explicit(self):
        ledger, _ = fresh()
        gate = ApprovalGate(ledger)
        aid = gate.request("production_deploy", "first deploy of brightpaths",
                           "COO", "coo.launch-runbook")
        self.assertEqual(gate.status(aid), "pending")
        self.assertEqual(len(gate.pending()), 1)
        # the request itself is Ledger-logged as needs_approval
        entry = ledger.recent(1)[0]
        self.assertEqual(entry["status"], "needs_approval")
        self.assertEqual(entry["approval_ref"], aid)

        gate.decide(aid, "approved")
        self.assertEqual(gate.status(aid), "approved")
        self.assertEqual(gate.pending(), [])
        # the decision is Ledger-logged and attributed to the Chairperson
        entry = ledger.recent(1)[0]
        self.assertEqual(entry["action_type"], "approval_decision")
        self.assertIn("chairperson", entry["agent_id"])

    def test_double_decision_rejected(self):
        ledger, _ = fresh()
        gate = ApprovalGate(ledger)
        aid = gate.request("contract_signature", "affiliate TOS", "LEGAL",
                           "legal.contract-review")
        gate.decide(aid, "rejected")
        with self.assertRaises(ApprovalError):
            gate.decide(aid, "approved")

    def test_invalid_decision_rejected(self):
        ledger, _ = fresh()
        gate = ApprovalGate(ledger)
        aid = gate.request("production_deploy", "x", "COO", "coo.launch-runbook")
        with self.assertRaises(ApprovalError):
            gate.decide(aid, "maybe")

    def test_spend_request_within_ceiling_auto_logs(self):
        ledger, _ = fresh()
        decision = request_spend(0.0, "free tier only", "CMO",
                                 "cmo.ad-creative", ledger)
        self.assertTrue(decision.approved)

    def test_spend_request_above_ceiling_halts(self):
        ledger, _ = fresh()
        decision = request_spend(5.0, "ads pilot", "CMO",
                                 "cmo.ad-creative", ledger)
        self.assertFalse(decision.approved)
        self.assertEqual(decision.status, "needs_approval")
        self.assertIsNotNone(decision.approval_id)
        gate = ApprovalGate(ledger)
        self.assertEqual(gate.status(decision.approval_id), "pending")


class TestPricingMath(unittest.TestCase):
    def test_cost_per_task_from_cmo_ledger_activity(self):
        ledger, router = fresh()
        # CMO activity lands in the Ledger (the cross-department handoff medium)
        ledger.log("CMO", "cmo.seo-audit", "seo_scan", "success")
        ledger.log("CMO", "cmo.seo-audit", "model_call", "success",
                   cost_tokens=120)
        out = PricingMath(ledger, router).run({})
        self.assertEqual(out["status"], "success")
        report = out["result"]["cost_per_task"]
        self.assertIn("cmo.seo-audit", report)
        self.assertEqual(report["cmo.seo-audit"]["tokens_per_task"], 120.0)
        # snapshot readable from Registry by any department
        reg = Registry(ledger.conn, ledger)
        self.assertIn("cmo.seo-audit", reg.get("CFO", "cost_per_task"))

    def test_cost_rise_flagged(self):
        ledger, router = fresh()
        ledger.log("CMO", "cmo.ai-seo", "ai_engine_optimization", "success")
        ledger.log("CMO", "cmo.ai-seo", "model_call", "success", cost_tokens=100)
        agent = PricingMath(ledger, router)
        agent.run({})
        # same task count, 4x the tokens -> cost/task quadruples
        ledger.log("CMO", "cmo.ai-seo", "model_call", "success", cost_tokens=300)
        out = agent.run({})
        flags = out["result"]["cost_rise_flags"]
        self.assertTrue(any(f["agent_id"] == "cmo.ai-seo" for f in flags))

    def test_empty_ledger_fails_dod(self):
        ledger, router = fresh()
        out = PricingMath(ledger, router).run({})
        self.assertEqual(out["status"], "failed")


class TestCEOCycle(unittest.TestCase):
    def tearDown(self):
        kill_switch.resume()

    def make_ceo(self):
        ledger, router = fresh()
        return ledger, CEO(ledger, router)

    def test_full_cycle_dry_run(self):
        ledger, ceo = self.make_ceo()
        out = ceo.run_cycle()
        by_agent = {r["agent_id"]: r for r in out["results"]}
        # brightpaths allocated from venture.properties and audited clean
        self.assertIn("cmo.seo-audit", by_agent)
        self.assertEqual(by_agent["cmo.seo-audit"]["status"], "success")
        # CFO ran after CMO and costed its activity via the Ledger
        self.assertIn("cfo.pricing-math", by_agent)
        self.assertEqual(by_agent["cfo.pricing-math"]["status"], "success")
        self.assertIn("cmo.seo-audit",
                      by_agent["cfo.pricing-math"]["result"]["cost_per_task"])
        # the cycle itself is Ledger-logged under the CEO
        entries = [e for e in ledger.recent(50)
                   if e["action_type"] == "operating_loop_cycle"]
        self.assertEqual(len(entries), 1)

    def test_brief_obeys_persona_rules(self):
        _, ceo = self.make_ceo()
        out = ceo.run_cycle()
        brief = out["brief"]
        self.assertLessEqual(len(brief.split()), 200)
        self.assertIn("Recommended next action:", brief)
        # never fabricates revenue: no revenue data -> says so explicitly
        self.assertIn("no revenue data", brief.lower())

    def test_pending_approval_surfaces_in_brief(self):
        ledger, ceo = self.make_ceo()
        ceo.gate.request("production_deploy", "launch brightpaths", "COO",
                         "coo.launch-runbook")
        out = ceo.run_cycle()
        self.assertIn("pending approval", out["brief"])
        self.assertIn("Decide the pending approvals",
                      out["brief"].split("Recommended next action:")[1])

    def test_kill_switch_halts_ceo(self):
        _, ceo = self.make_ceo()
        kill_switch.pause("phase-2 test")
        with self.assertRaises(kill_switch.SystemPaused):
            ceo.run_cycle()


if __name__ == "__main__":
    unittest.main(verbosity=2)
