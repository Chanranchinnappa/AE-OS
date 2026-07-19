"""Uptime/deploy sentinel — watches live venture properties (COO domain).

Checks, all deterministic and token-free:
  1. Property homepage returns HTTP 200.
  2. sitemap.xml is reachable and every <loc> URL in it returns 200.
  3. The property's last Pages deploy workflow run concluded 'success'
     (via `gh` CLI; skipped gracefully when gh is unavailable).

Per 06_MEMORY_SYSTEM.md access rules: sentinels are read-only; their single
write is their own alert record. On anomaly the caller (watch.py) wakes the
CEO — the sentinel itself never remediates anything.
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Callable

from core import kill_switch
from memory.ledger import Ledger

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "config" / "settings.json"
HTTP_TIMEOUT = 20

HttpGet = Callable[[str], tuple[int | None, str]]
GhRun = Callable[[list[str]], tuple[int, str]]


def _default_http_get(url: str) -> tuple[int | None, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ae-os-sentinel"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            return r.status, r.read(65536).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # DNS failure, timeout, TLS — all are outages
        return None, str(e)


def _default_gh_run(args: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(["gh", *args], capture_output=True, text=True,
                           timeout=30)
        return p.returncode, p.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 127, ""


class UptimeSentinel:
    department = "COO"
    agent_id = "coo.sentinel-uptime"

    def __init__(self, ledger: Ledger | None = None,
                 http_get: HttpGet | None = None,
                 gh_run: GhRun | None = None):
        self.ledger = ledger or Ledger()
        self._http_get = http_get or _default_http_get
        self._gh_run = gh_run or _default_gh_run

    def _check_url(self, label: str, url: str) -> dict[str, Any]:
        code, _ = self._http_get(url)
        return {"check": label, "ok": code == 200,
                "detail": f"{url} -> {code if code is not None else 'unreachable'}"}

    def check_property(self, prop: dict[str, Any]) -> list[dict[str, Any]]:
        base = prop.get("url", "").rstrip("/")
        checks = [self._check_url("homepage 200", base + "/")]

        code, body = self._http_get(base + "/sitemap.xml")
        if code == 200:
            checks.append({"check": "sitemap reachable", "ok": True,
                           "detail": base + "/sitemap.xml"})
            for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body):
                checks.append(self._check_url("sitemap url 200", loc))
        else:
            checks.append({"check": "sitemap reachable", "ok": False,
                           "detail": f"{base}/sitemap.xml -> {code}"})

        workflow = prop.get("deploy_workflow")
        if workflow:
            rc, out = self._gh_run(["run", "list", "--workflow", workflow,
                                    "--limit", "1", "--json", "conclusion"])
            if rc != 0:
                checks.append({"check": "last deploy succeeded", "ok": True,
                               "detail": "gh unavailable — deploy check skipped"})
            else:
                try:
                    conclusion = (json.loads(out) or [{}])[0].get("conclusion")
                except (json.JSONDecodeError, IndexError):
                    conclusion = None
                checks.append({"check": "last deploy succeeded",
                               "ok": conclusion == "success",
                               "detail": f"workflow {workflow}: {conclusion}"})
        return checks

    def watch(self) -> dict[str, Any]:
        """Run all checks for every live property; log one alert record."""
        kill_switch.guard()
        cfg = (json.loads(SETTINGS_PATH.read_text())
               if SETTINGS_PATH.exists() else {})
        props = [p for p in cfg.get("venture", {}).get("properties", [])
                 if p.get("status") == "live" and p.get("url")]

        all_checks, anomalies = [], []
        for prop in props:
            checks = self.check_property(prop)
            for c in checks:
                c["property"] = prop["name"]
            all_checks.extend(checks)
            anomalies.extend(c for c in checks if not c["ok"])

        entry_id = self.ledger.log(
            department=self.department, agent_id=self.agent_id,
            action_type="sentinel_watch",
            status="failed" if anomalies else "success",
            inputs={"properties": [p["name"] for p in props]},
            outputs={"checks_run": len(all_checks), "anomalies": anomalies,
                     "route_on_anomaly": "wake CEO for early partial cycle; "
                                         "COO incident-postmortem when built"},
        )
        return {"properties_watched": len(props), "checks_run": len(all_checks),
                "anomalies": anomalies, "ledger_id": entry_id}
