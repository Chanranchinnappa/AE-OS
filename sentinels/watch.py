"""Sentinel runner — one pass over every registered sentinel.

On anomaly, wakes the CEO for an early partial Operating Loop cycle
(04_OPERATING_LOOP.md trigger conditions). The sentinel detects; the CEO
decides; departments act.

CLI:
    python -m sentinels.watch             # watch + wake CEO on anomaly
    python -m sentinels.watch --no-cycle  # watch only (report, never wake)

Schedule it (Windows) for true always-on behavior, e.g. hourly:
    schtasks /Create /SC HOURLY /TN AE-OS-Sentinel ^
      /TR "python -m sentinels.watch" /ST 09:00
"""
from __future__ import annotations

import sys

from . import SENTINELS


def run(trigger_cycle: bool = True) -> int:
    anomalies_total = 0
    for cls in SENTINELS:
        result = cls().watch()
        anomalies = result["anomalies"]
        anomalies_total += len(anomalies)
        print(f"{cls.agent_id}: {result['checks_run']} checks over "
              f"{result['properties_watched']} properties, "
              f"{len(anomalies)} anomalies")
        for a in anomalies:
            print(f"  ANOMALY [{a['property']}] {a['check']}: {a['detail']}")

    if anomalies_total and trigger_cycle:
        print("Waking CEO for early partial cycle...")
        from core.ceo import CEO
        out = CEO().run_cycle()
        print(out["brief"])
    return 1 if anomalies_total else 0


if __name__ == "__main__":
    raise SystemExit(run(trigger_cycle="--no-cycle" not in sys.argv))
