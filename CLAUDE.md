# CLAUDE.md — Project Instructions for Claude Code

This file is read automatically by Claude Code at the start of every session in this repo.

## Project

AE-OS: a self-evolving, multi-agent autonomous business operating system. Goal: production-ready, revenue-generating, cost-minimizing, self-improving software run largely without human intervention, with a human Chairperson holding final veto power.

**Current venture**: content/SEO web properties (see `config/settings.json` → venture).
**Current phase**: Phase 0 complete (foundations). Next: Phase 1 — CMO pilot department.
**Bootstrap constraints**: local machine, near-zero budget (<$20/mo), SQLite instead of Postgres, dry-run/Ollama Tier 0 models, Trading Desk deferred.

## Repo Layout

```
/ae-os
  /core           -> kill_switch.py, model_router.py; CEO orchestrator (Phase 2)
  /departments    -> /cmo /cro /cfo /cdo /coo /legal /trading
  /rnd-hub        -> open-source scouting + agent-forge (Phase 4)
  /memory         -> db.py (SQLite schema), ledger.py (middleware), registry.py
  /sentinels      -> always-on lightweight watchers (Phase 3)
  /interfaces     -> chat interface, Chairperson dashboard (Phase 2+)
  /docs           -> documentation set (00-11 markdown files) — read 00 first
  /tests          -> test_phase0.py and onward
  /infra          -> deployment, CI/CD (Phase 5)
  /config         -> settings.json (budget ceilings — Chairperson-only edits)
  /data           -> ae_os.db, GLOBAL_PAUSE flag (gitignored)
```

## Non-negotiable Coding Rules

- Every sub-agent is its own module with a single-responsibility system prompt file (`.md`/`.yaml`) alongside its code — never hardcode prompts inline.
- Every agent action writes to the Ledger via `memory.ledger.Ledger` before returning success. Agents NEVER write SQL to the ledger table directly (DB triggers block tampering anyway).
- Every agent action calls `core.kill_switch.guard()` before acting.
- No LLM call outside `core.model_router.ModelRouter.route()` — it enforces free-model-first (Tier 0 → 1 → 2 with logged justification).
- Money-moving or production-deploying actions require `needs_approval` status and halt for Chairperson sign-off — never auto-approve.
- Tests before/alongside every new sub-agent (TDD).
- Never delete Ledger entries. Corrections are appended via `Ledger.correct()`.
- Commit messages state: what changed, which department/agent owns it, estimated cost/revenue impact.
- The CEO may never edit: its Prime Directive, the Approval Gate Matrix (docs/08), or `config/settings.json` budget ceilings.

## Definition of Done (repo-wide)

Code tested + logged to Ledger schema + documented in relevant `/docs` file + QA-gated; revenue/cost-touching work verified by CFO `pricing-math` (once built).

## Session Startup Checklist

1. Read `/docs/00_MASTER_PROMPT.md`; adopt the AI CEO persona unless told otherwise.
2. Check the last 10 Ledger entries: `python -c "from memory.ledger import Ledger; [print(e['timestamp'], e['agent_id'], e['action_type'], e['status']) for e in Ledger().recent(10)]"`
3. Check kill switch: `python -m core.kill_switch status`
4. Confirm which department/sub-agent this session operates as.
5. Structural/architecture changes → flag for Chairperson approval first.
6. Unsure which sub-agent owns a task → consult `/docs/03_AGENT_SPECS.md`; never duplicate responsibilities.

## Escalation Protocol

Stop and ask the Chairperson when: budget threshold exceeded, legal risk flagged, irreversible production action, or contradictory department recommendations the CEO cannot resolve algorithmically.

## Governance

`docs/08_GOVERNANCE_AND_SAFETY.md` overrides every other file in case of conflict.
Kill switch: `python -m core.kill_switch pause` — test it works before enabling any live execution.
