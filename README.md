# AE-OS

Autonomous Enterprise Operating System. Human Chairperson holds final veto; an AI CEO orchestrates 7 departments of single-job sub-agents. Full blueprint in `/docs` (read `docs/README.md` for order; `docs/08` overrides everything).

**Status**: Phase 0 complete. Venture: content/SEO sites. Bootstrap constraints: local, <$20/mo, SQLite, dry-run/Ollama models, Trading Desk deferred.

## What exists now

| Component | File | Verified by |
|---|---|---|
| Append-only Ledger (DB-enforced immutability) | `memory/db.py`, `memory/ledger.py` | `tests/test_phase0.py` |
| Company Registry (owner-only writes, diffs mirrored to Ledger, secret guard) | `memory/registry.py` | tests |
| Model Router (Tier 0→1→2, escalation requires logged failures, every call costed) | `core/model_router.py` | tests |
| Kill switch (global pause, fail-safe, checked before every action) | `core/kill_switch.py` | tests + CLI |

## Quickstart (Windows, Python 3.10+)

```bash
cd ae-os
python -m unittest discover tests        # 16 tests, all must pass
python -m core.kill_switch status        # governance check
python -m core.kill_switch pause         # THE red button
python -m core.kill_switch resume
```

No dependencies — stdlib only. Data lives in `/data` (gitignored).

## Next steps

1. Install [Ollama](https://ollama.com), pull a small model, set `tier0_provider: "ollama"` in `config/settings.json` — real Tier 0 at zero cost.
2. Set your real budget ceilings in `config/settings.json` (Chairperson-only file).
3. Open this folder in Claude Code and give it the First Command from `docs/10_BUILD_ROADMAP.md` to start Phase 1 (CMO pilot).
