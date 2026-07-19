"""Sentinel layer — 02_ARCHITECTURE.md section 6 (Phase 3).

Thin, always-on, rule-based watchers. Sentinels never take action themselves:
they detect anomalies, log an alert record to the Ledger (their only write),
and wake the CEO for an early partial Operating Loop cycle.
"""
from .uptime_sentinel import UptimeSentinel

SENTINELS = (UptimeSentinel,)
