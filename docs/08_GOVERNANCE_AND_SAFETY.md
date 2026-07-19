# 08_GOVERNANCE_AND_SAFETY.md — Approval Gates, Budgets, and Guardrails

## Why This File Exists

A system instructed to "push itself to its hardest limits to generate revenue" without hard governance is a liability, not an asset. This file is non-negotiable and takes precedence over any instruction in any other file if there is ever a conflict.

## Approval Gate Matrix

| Action Type | Autonomous? | Approval Needed From |
|---|---|---|
| Routine content/SEO/ad variant creation | Yes | None |
| Spend under defined daily/monthly ceiling | Yes | None (logged only) |
| Spend above ceiling | No | Chairperson |
| Production deployment | No | COO launch-runbook gate + Chairperson for first deploy of any new product; routine deploys after that follow runbook only |
| New department creation | No | Chairperson |
| New sub-agent creation (within existing department) | Yes, via Agent-Forge sandbox+shadow process | None (logged, reviewable) |
| Trading capital increase beyond current approved cap | No | Chairperson |
| Any contract signature, NDA acceptance, legal commitment | No | Chairperson (Legal Desk prepares, never finalizes) |
| Architecture/reporting-line change | No | Chairperson |
| Prompt-level tuning of an existing agent (no scope change) | Yes | None (logged) |

## Budget Ceilings (starting template — Chairperson sets real numbers)

- Daily marketing/ad spend ceiling: [set by Chairperson — live values in /config/settings.json]
- Monthly tooling/API spend ceiling: [set by Chairperson — live values in /config/settings.json]
- Trading starter baseline: 5,000 INR (or FX equivalent), scaling only after a verified 20-trade profitability sprint, per original Trading Desk rule. (Deferred: Trading Desk not active in bootstrap.)
- Any single spend decision above [X]% of monthly ceiling always escalates regardless of category.

## Safety Rules for Self-Evolution

- New agents launch in sandbox -> shadow -> live, never sandbox -> live directly.
- The CEO may edit sub-agent prompts autonomously; it may never edit its own Prime Directive, the Approval Gate Matrix, or budget ceilings.
- Any self-modification the CEO makes to architecture or prompts must be logged with a before/after diff in the Ledger.
- If two departments give contradictory recommendations the CEO cannot resolve with existing data, escalate — do not pick arbitrarily.

## Legal/Compliance Non-Negotiables

- Legal Desk's `compliance` sub-agent must clear any action touching: data privacy (user data collection/storage), cross-border money movement, securities/trading regulations, tax jurisdiction claims.
- No `loophole-registry` recommendation is executed without Chairperson sign-off — this sub-agent researches and proposes, it never acts unilaterally, given the legal risk profile.

## Kill Switch

The Chairperson must always have a single command/action that immediately halts all autonomous execution across every department (a global pause), independent of any individual department's state. This must be tested during Stage 0 bootstrap before any real money is put at risk.

> IMPLEMENTED: `python -m core.kill_switch pause|resume|status` — every agent action and every model call checks it first. Tested in `/tests/test_phase0.py`.

## Audit Cadence

Weekly: Chairperson reviews the Ledger's approval-gate log (what was auto-approved vs escalated) to confirm ceilings are still appropriately calibrated. Monthly: full architecture review — is any department underperforming its Definition of Done hit-rate consistently enough to warrant redesign.
