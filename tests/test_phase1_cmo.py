"""Phase 1 verification — CMO department pilot (10_BUILD_ROADMAP.md).

Covers, per CLAUDE.md non-negotiables:
  - full roster present and matching 03_AGENT_SPECS.md
  - every agent action logs to the Ledger with correct schema
  - DoD checks actually fail bad output (not rubber stamps)
  - kill switch halts every agent
  - money gate: ad spend above ceiling -> needs_approval, never auto-run
  - prompt files exist alongside each agent module (never inline)

Run: python -m unittest tests.test_phase1_cmo -v
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
from core.model_router import ModelRouter, RouterConfig
from memory import db as _db
from memory.ledger import Ledger

from departments.cmo import (ROSTER, AiSeo, AdCreative, CroContent,
                             CMODepartment, MktgPsychology, ProgrammaticSeo,
                             SeoAudit)

SPEC_ROSTER = {"seo-audit", "programmatic-seo", "ai-seo", "cro-content",
               "ad-creative", "mktg-psychology"}


def fresh():
    conn = _db.connect(":memory:")
    ledger = Ledger(conn)
    router = ModelRouter(ledger, RouterConfig())  # dry_run tier 0
    return ledger, router


def make(cls):
    ledger, router = fresh()
    return ledger, cls(ledger, router)


SEO_TASK = {"site": "site-a.com", "pages": [
    {"url": "/good", "title": "Good page", "meta_description": "d",
     "h1": "h", "word_count": 900, "internal_links": ["/other"]},
    {"url": "/bad", "title": "", "meta_description": "", "h1": "",
     "word_count": 50, "internal_links": []},
]}


class TestRoster(unittest.TestCase):
    def test_matches_agent_specs(self):
        self.assertEqual({cls.name for cls in ROSTER}, SPEC_ROSTER)

    def test_prompt_file_alongside_every_agent(self):
        for cls in ROSTER:
            module_file = Path(sys.modules[cls.__module__].__file__)
            prompt = module_file.with_suffix(".md")
            self.assertTrue(prompt.exists(), f"missing prompt file: {prompt}")
            _, agent = make(cls)
            self.assertIn(f"cmo.{cls.name}", agent.system_prompt())


class TestSeoAudit(unittest.TestCase):
    def test_issues_scored_with_fixes(self):
        ledger, agent = make(SeoAudit)
        out = agent.run(dict(SEO_TASK))
        self.assertEqual(out["status"], "success")
        issues = out["result"]["issues"]
        self.assertTrue(issues, "bad page should raise issues")
        for i in issues:
            self.assertIsInstance(i["severity_score"], int)
            self.assertTrue(i["fix"])
        # logged to Ledger with correct identity
        entries = [e for e in ledger.recent(20) if e["agent_id"] == "cmo.seo-audit"
                   and e["action_type"] == "seo_scan"]
        self.assertEqual(len(entries), 1)

    def test_empty_scan_fails_dod(self):
        _, agent = make(SeoAudit)
        out = agent.run({"site": "site-a.com", "pages": []})
        self.assertEqual(out["status"], "failed")


class TestProgrammaticSeo(unittest.TestCase):
    def test_pages_qa_and_index_check(self):
        _, agent = make(ProgrammaticSeo)
        out = agent.run({
            "template": "Best {keyword} guide | site-a",
            "dataset": [{"keyword": "solar lamps"}, {"keyword": "garden lights"}],
        })
        self.assertEqual(out["status"], "success")
        self.assertTrue(all(p["qa_passed"] for p in out["result"]["pages"]))
        self.assertTrue(out["result"]["index_check"]["scheduled_for"])

    def test_qa_failure_fails_dod(self):
        _, agent = make(ProgrammaticSeo)
        # No template -> empty titles -> QA fails -> DoD fails
        out = agent.run({"template": "", "dataset": [{"keyword": "solar lamps"}]})
        self.assertEqual(out["status"], "failed")

    def test_truthfulness_gate_rejects_seller_voice(self):
        _, agent = make(ProgrammaticSeo)
        page = {"title": "Solar for garden steps", "keyword": "garden steps",
                "body": "We've developed a range of solar lights for garden steps.",
                "source_row": {"keyword": "garden steps"}}
        failures = agent._qa(page)
        self.assertTrue(any("seller-voice" in f for f in failures), failures)

    def test_truthfulness_gate_rejects_unsourced_numbers(self):
        _, agent = make(ProgrammaticSeo)
        page = {"title": "Solar for garden steps", "keyword": "garden steps",
                "body": "Solar lights on garden steps typically run for 10 hours nightly.",
                "source_row": {"keyword": "garden steps"}}
        failures = agent._qa(page)
        self.assertTrue(any("unsourced numeric claim" in f for f in failures), failures)

    def test_meta_commentary_scrubbed(self):
        _, agent = make(ProgrammaticSeo)
        raw = ("Here is the filled-in landing page template:\n\n"
               "Solar lights suit garden steps well.\n"
               "Note: I've avoided using \"we\", \"our\", \"us\".")
        scrubbed = agent._scrub(raw)
        self.assertEqual(scrubbed, "Solar lights suit garden steps well.")
        # scrubbed content no longer trips the seller-voice gate
        page = {"title": "T", "keyword": "garden steps", "body": scrubbed * 3,
                "source_row": {"keyword": "garden steps"}}
        self.assertEqual(agent._qa(page), [])

    def test_truthfulness_gate_allows_sourced_numbers(self):
        _, agent = make(ProgrammaticSeo)
        page = {"title": "Solar for garden steps", "keyword": "garden steps",
                "body": "Solar lights on garden steps typically run for 10 hours nightly.",
                "source_row": {"keyword": "garden steps", "run_time": "10 hours"}}
        failures = agent._qa(page)
        self.assertEqual(failures, [])


class TestAiSeo(unittest.TestCase):
    def test_citations_from_provided_sources(self):
        _, agent = make(AiSeo)
        out = agent.run({"content_brief": "why solar lamps",
                         "sources": [{"url": "https://energy.gov/x", "fact": "f1"}]})
        self.assertEqual(out["status"], "success")
        self.assertEqual(out["result"]["citations"], ["https://energy.gov/x"])

    def test_no_sources_fails_dod(self):
        _, agent = make(AiSeo)
        out = agent.run({"content_brief": "why solar lamps", "sources": []})
        self.assertEqual(out["status"], "failed")

    def test_hallucinated_citation_detected(self):
        _, agent = make(AiSeo)
        bad = {"citations": ["https://made-up.example"],
               "claims": [{"claim": "x", "source": "https://made-up.example"}],
               "allowed_sources": ["https://energy.gov/x"]}
        ok, notes = agent.check_dod(bad)
        self.assertFalse(ok)
        self.assertTrue(any("hallucinated" in n for n in notes))

    def test_truthfulness_gate_on_draft(self):
        _, agent = make(AiSeo)
        bad = {"citations": ["https://energy.gov/x"],
               "claims": [{"claim": "x", "source": "https://energy.gov/x"}],
               "allowed_sources": ["https://energy.gov/x"],
               "content_violations": ["seller-voice claim ('we...')"]}
        ok, notes = agent.check_dod(bad)
        self.assertFalse(ok)
        self.assertTrue(any("truthfulness gate" in n for n in notes))


class TestCroContent(unittest.TestCase):
    def test_full_test_design(self):
        _, agent = make(CroContent)
        out = agent.run({"page": "/pricing", "hypothesis": "urgency headline lifts CTR",
                        "baseline_conversion_rate": 0.05,
                        "min_detectable_effect": 0.02,
                        "baseline_visitors_per_day": 400})
        self.assertEqual(out["status"], "success")
        ssc = out["result"]["sample_size_check"]
        self.assertGreater(ssc["required_per_arm"], 0)
        self.assertTrue(ssc["feasible"])

    def test_missing_baseline_fails_dod(self):
        _, agent = make(CroContent)
        out = agent.run({"page": "/pricing", "hypothesis": "h"})
        self.assertEqual(out["status"], "failed")


class TestAdCreative(unittest.TestCase):
    def test_variants_tagged_with_hypothesis(self):
        _, agent = make(AdCreative)
        out = agent.run({"product": "solar lamp",
                         "hypotheses": ["fear of dark sells", "eco angle sells"],
                         "requested_daily_spend": 0})
        self.assertEqual(out["status"], "success")
        for v in out["result"]["variants"]:
            self.assertTrue(v["hypothesis"])

    def test_spend_above_ceiling_needs_approval(self):
        ledger, agent = make(AdCreative)
        out = agent.run({"product": "solar lamp", "hypotheses": ["h1"],
                         "requested_daily_spend": 5.0})
        self.assertEqual(out["status"], "needs_approval")
        entry = next(e for e in ledger.recent(20)
                     if e["agent_id"] == "cmo.ad-creative"
                     and e["action_type"] == "generate_ad_variants")
        self.assertEqual(entry["status"], "needs_approval")


class TestMktgPsychology(unittest.TestCase):
    def test_recommendations_backed_by_data(self):
        _, agent = make(MktgPsychology)
        out = agent.run({"audience": "homeowners",
                         "funnel_data": [{"stage": "cart", "drop_off_pct": 60}]})
        self.assertEqual(out["status"], "success")
        for rec in out["result"]["recommendations"]:
            self.assertTrue(rec["evidence"]["metrics"])

    def test_no_data_fails_dod(self):
        _, agent = make(MktgPsychology)
        out = agent.run({"audience": "homeowners", "funnel_data": []})
        self.assertEqual(out["status"], "failed")


class TestKillSwitchHaltsCMO(unittest.TestCase):
    def tearDown(self):
        kill_switch.resume()

    def test_every_agent_blocked_when_paused(self):
        kill_switch.pause("phase-1 test")
        for cls in ROSTER:
            ledger, agent = make(cls)
            with self.assertRaises(kill_switch.SystemPaused):
                agent.run({})
            self.assertEqual(ledger.recent(5), [], "paused agent must log nothing")


class TestDepartmentCycle(unittest.TestCase):
    def test_dry_run_cycle_logs_everything(self):
        ledger, router = fresh()
        dept = CMODepartment(ledger, router)
        dept.publish_roster()
        out = dept.run_cycle({
            "seo-audit": dict(SEO_TASK),
            "ai-seo": {"content_brief": "b",
                       "sources": [{"url": "https://energy.gov/x", "fact": "f"}]},
        })
        self.assertEqual(out["summary"]["dispatched"], 2)
        self.assertEqual(out["summary"]["failed"], 0)
        # cost tracking: dry-run model calls still log token counts
        self.assertGreater(out["summary"]["cumulative_cost"]["tokens"], 0)
        types = [e["action_type"] for e in ledger.recent(50)]
        self.assertIn("cycle_summary", types)
        self.assertIn("registry_update", types)
        self.assertIn("model_call", types)

    def test_unknown_agent_rejected(self):
        ledger, router = fresh()
        dept = CMODepartment(ledger, router)
        with self.assertRaises(ValueError):
            dept.run_cycle({"growth-hacker": {}})


if __name__ == "__main__":
    unittest.main(verbosity=2)
