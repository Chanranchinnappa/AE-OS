"""Phase 3 — Sentinel layer, first watcher (uptime/deploy).

Run: python -m unittest tests.test_phase3_sentinels -v
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
from memory import db as _db
from memory.ledger import Ledger
from sentinels.uptime_sentinel import UptimeSentinel

SITEMAP = """<?xml version="1.0"?>
<urlset><url><loc>https://x.test/AE-OS/a.html</loc></url>
<url><loc>https://x.test/AE-OS/b.html</loc></url></urlset>"""

PROP = {"name": "testprop", "status": "live", "url": "https://x.test/AE-OS/",
        "deploy_workflow": "wf"}


def make(statuses: dict[str, int | None], gh_out='[{"conclusion":"success"}]',
         gh_rc=0):
    """Sentinel with a fake web: statuses maps URL -> HTTP code."""
    ledger = Ledger(_db.connect(":memory:"))

    def http_get(url):
        code = statuses.get(url, 200)
        body = SITEMAP if url.endswith("sitemap.xml") and code == 200 else ""
        return code, body

    return ledger, UptimeSentinel(ledger, http_get=http_get,
                                  gh_run=lambda a: (gh_rc, gh_out))


class TestUptimeSentinel(unittest.TestCase):
    def test_all_healthy(self):
        _, s = make({})
        checks = s.check_property(PROP)
        self.assertTrue(all(c["ok"] for c in checks))
        # homepage + sitemap + 2 sitemap urls + deploy = 5 checks
        self.assertEqual(len(checks), 5)

    def test_dead_article_detected(self):
        _, s = make({"https://x.test/AE-OS/b.html": 404})
        bad = [c for c in s.check_property(PROP) if not c["ok"]]
        self.assertEqual(len(bad), 1)
        self.assertIn("b.html -> 404", bad[0]["detail"])

    def test_site_unreachable_detected(self):
        _, s = make({"https://x.test/AE-OS/": None,
                     "https://x.test/AE-OS/sitemap.xml": None})
        bad = [c for c in s.check_property(PROP) if not c["ok"]]
        self.assertGreaterEqual(len(bad), 2)

    def test_failed_deploy_detected(self):
        _, s = make({}, gh_out='[{"conclusion":"failure"}]')
        bad = [c for c in s.check_property(PROP) if not c["ok"]]
        self.assertTrue(any("deploy" in c["check"] for c in bad))

    def test_gh_unavailable_skips_gracefully(self):
        _, s = make({}, gh_rc=127, gh_out="")
        deploy = [c for c in s.check_property(PROP)
                  if c["check"] == "last deploy succeeded"]
        self.assertTrue(deploy[0]["ok"])
        self.assertIn("skipped", deploy[0]["detail"])

    def test_watch_logs_alert_record(self):
        # watch() reads real settings (brightpaths, live) but with a fake web
        ledger, s = make({})
        out = s.watch()
        self.assertEqual(out["anomalies"], [])
        entry = ledger.recent(1)[0]
        self.assertEqual(entry["action_type"], "sentinel_watch")
        self.assertEqual(entry["status"], "success")
        self.assertEqual(entry["agent_id"], "coo.sentinel-uptime")

    def test_watch_anomaly_logged_as_failed(self):
        ledger, s = make({"https://chanranchinnappa.github.io/AE-OS/": 404})
        out = s.watch()
        self.assertTrue(out["anomalies"])
        self.assertEqual(ledger.recent(1)[0]["status"], "failed")

    def test_kill_switch_blocks_sentinel(self):
        ledger, s = make({})
        kill_switch.pause("phase-3 test")
        try:
            with self.assertRaises(kill_switch.SystemPaused):
                s.watch()
            self.assertEqual(ledger.recent(5), [])
        finally:
            kill_switch.resume()


if __name__ == "__main__":
    unittest.main(verbosity=2)
