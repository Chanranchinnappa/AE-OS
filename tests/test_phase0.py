"""Phase 0 verification suite.

Covers the three non-negotiables from 10_BUILD_ROADMAP.md Phase 0:
  1. Ledger immutability (append-only, middleware-only writes)
  2. Model Router tier policy (free-first, justified escalation, cost logging)
  3. Kill switch (halts everything, tested before anything goes live)

Run: python -m pytest tests/ -v   (or: python -m unittest discover tests)
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Isolate the kill switch to a local temp file so tests never touch (or race on)
# the real data/GLOBAL_PAUSE flag.
os.environ["AE_OS_PAUSE_FILE"] = os.path.join(tempfile.mkdtemp(), "GLOBAL_PAUSE")

from memory import db as _db
from memory.ledger import Ledger, LedgerError
from memory.registry import Registry, RegistryError
from core import kill_switch
from core.model_router import ModelRouter, RouterConfig, EscalationDenied


def fresh() -> tuple:
    conn = _db.connect(":memory:")
    ledger = Ledger(conn)
    return conn, ledger


class TestLedgerImmutability(unittest.TestCase):
    def test_log_and_read(self):
        _, ledger = fresh()
        eid = ledger.log("CMO", "cmo.seo-audit", "scan", "success",
                         cost_tokens=100)
        self.assertEqual(len(ledger.recent(10)), 1)
        self.assertEqual(ledger.recent(1)[0]["id"], eid)

    def test_update_forbidden(self):
        conn, ledger = fresh()
        ledger.log("CMO", "cmo.seo-audit", "scan", "success")
        with self.assertRaises(sqlite3.DatabaseError):
            conn.execute("UPDATE ledger SET status='failed'")

    def test_delete_forbidden(self):
        conn, ledger = fresh()
        ledger.log("CMO", "cmo.seo-audit", "scan", "success")
        with self.assertRaises(sqlite3.DatabaseError):
            conn.execute("DELETE FROM ledger")

    def test_corrections_append(self):
        _, ledger = fresh()
        eid = ledger.log("CFO", "cfo.pricing-math", "cost_calc", "success")
        cid = ledger.correct(eid, department="CFO", agent_id="cfo.pricing-math",
                             action_type="cost_calc", status="success")
        rows = ledger.recent(10)
        self.assertEqual(len(rows), 2)
        corr = next(r for r in rows if r["id"] == cid)
        self.assertEqual(corr["corrects"], eid)

    def test_invalid_department_rejected(self):
        _, ledger = fresh()
        with self.assertRaises(LedgerError):
            ledger.log("HR", "hr.nobody", "hire", "success")

    def test_cost_aggregation(self):
        _, ledger = fresh()
        ledger.log("CMO", "cmo.seo-audit", "scan", "success", cost_tokens=100)
        ledger.log("CDO", "cdo.superpowers", "design", "success",
                   cost_tokens=50, cost_currency=0.01)
        totals = ledger.total_cost()
        self.assertEqual(totals["tokens"], 150)
        self.assertAlmostEqual(totals["currency"], 0.01)


class TestRegistry(unittest.TestCase):
    def test_owner_can_write_and_mirror_to_ledger(self):
        conn, ledger = fresh()
        reg = Registry(conn, ledger)
        reg.set("CMO", "active_sites", ["site-a.com"], "cmo.seo-audit")
        self.assertEqual(reg.get("CMO", "active_sites"), ["site-a.com"])
        self.assertEqual(ledger.recent(1)[0]["action_type"], "registry_update")

    def test_cross_department_write_blocked(self):
        conn, ledger = fresh()
        reg = Registry(conn, ledger)
        with self.assertRaises(RegistryError):
            reg.set("CFO", "runway", {"months": 12}, "cmo.seo-audit")

    def test_raw_secrets_blocked(self):
        conn, ledger = fresh()
        reg = Registry(conn, ledger)
        with self.assertRaises(RegistryError):
            reg.set("CMO", "creds", {"api_key": "sk-123"}, "cmo.seo-audit")


class TestKillSwitch(unittest.TestCase):
    def setUp(self):
        kill_switch.resume()

    def tearDown(self):
        kill_switch.resume()

    def test_pause_and_guard(self):
        kill_switch.pause("test")
        self.assertTrue(kill_switch.is_paused())
        with self.assertRaises(kill_switch.SystemPaused):
            kill_switch.guard()

    def test_resume(self):
        kill_switch.pause("test")
        kill_switch.resume()
        kill_switch.guard()  # must not raise

    def test_router_respects_kill_switch(self):
        _, ledger = fresh()
        router = ModelRouter(ledger, RouterConfig())
        kill_switch.pause("test")
        with self.assertRaises(kill_switch.SystemPaused):
            router.route("hello", "cmo.seo-audit", "CMO", "t1")


class TestModelRouterPolicy(unittest.TestCase):
    def make(self):
        _, ledger = fresh()
        return ledger, ModelRouter(ledger, RouterConfig())

    def test_tier0_default_and_logged(self):
        ledger, router = self.make()
        resp = router.route("draft a title", "cmo.ad-creative", "CMO", "t1")
        self.assertEqual(resp.tier, 0)
        entry = ledger.recent(1)[0]
        self.assertEqual(entry["action_type"], "model_call")
        self.assertGreater(entry["cost_tokens"], 0)

    def test_tier1_denied_without_tier0_failure(self):
        _, router = self.make()
        with self.assertRaises(EscalationDenied):
            router.route("x", "cmo.ad-creative", "CMO", "t1", tier=1)

    def test_tier2_denied_without_both_failures(self):
        _, router = self.make()
        router.record_failure("t1", 0)
        with self.assertRaises(EscalationDenied):
            router.route("x", "cmo.ad-creative", "CMO", "t1", tier=2)

    def test_high_stakes_may_use_tier2_policywise(self):
        _, router = self.make()
        # Policy authorizes it; provider 'none' isn't wired, which is the
        # correct near-zero-budget failure mode.
        from core.model_router import RouterError
        with self.assertRaises(RouterError):
            router.route("review contract", "legal.contract-review", "LEGAL",
                         "t9", task_class="legal_risk", tier=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
