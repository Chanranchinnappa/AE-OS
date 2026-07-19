# 10_BUILD_ROADMAP.md — Getting from Zero to Production

## Phase 0 — Foundations (Week 1-2)

- [x] Set up repo structure per 01_CLAUDE_PROJECT_INSTRUCTIONS.md.
- [x] Stand up Ledger + Company Registry (SQLite bootstrap — Postgres+pgvector deferred to Phase 4, before Cognee).
- [x] Implement the Model Router (07_TECH_STACK_AND_INFRA.md) with Tier 0/1/2 routing and cost logging.
- [x] Implement the Ledger logging middleware — every agent action must pass through it.
- [x] Build the kill switch (08_GOVERNANCE_AND_SAFETY.md) and test it before anything else goes live.

## Phase 1 — Single Department Pilot (Week 3-5)

- [x] Department chosen: **CMO** (venture = content/SEO sites; closest to existing skillset).
- [x] Implement its full sub-agent roster from 03_AGENT_SPECS.md with real DoD checks. (`/departments/cmo/`, tested in `tests/test_phase1_cmo.py`)
- [x] Run the Operating Loop (04_OPERATING_LOOP.md) manually triggered, dry-run mode only. (Department-level cycle via `CMODepartment.run_cycle()`; full 8-step CEO loop is Phase 2.)
- [x] Validate: does every action actually log to the Ledger correctly? Does cost tracking work? (Verified: agent actions + model calls logged with token costs; ad-spend request above ceiling halted as `needs_approval`.)

## Phase 2 — CEO Orchestration Layer (Week 6-8)

- [x] Build the AI CEO orchestrator: ingestion, task allocation, verification, compilation steps. (`core/ceo.py`, `python -m core.ceo cycle`; deterministic bootstrap allocation)
- [x] Wire in the Voice/Chat Interface persona wrapper (00_MASTER_PROMPT.md tone rules). (Deterministic brief compiler in `CEO.compile_brief` — 200-word cap, mandatory recommended action, no fabricated revenue. Standalone chat interface still Phase 2+.)
- [x] Add a second and third department; test cross-department task handoff via Shared Memory (never direct calls). (CFO `pricing-math` costs CMO's work via Ledger reads; COO `launch-runbook` reads CMO audit results via Ledger and `sop-builder` cites Ledger provenance. No direct cross-department calls anywhere; tested in `tests/test_phase2_ceo.py` + `tests/test_phase2_coo.py`.)
- [x] Implement the Approval Gate Matrix (08_GOVERNANCE_AND_SAFETY.md) — test that spend/deploy/legal actions actually halt for approval. (`core/approval_gate.py` + Chairperson CLI `python -m core.approval_gate list|approve|reject`; halt behavior tested in `tests/test_phase2_ceo.py`)

## Phase 3 — Sentinel Layer + Remaining Departments (Month 3-4)

- [ ] Build lightweight Sentinels for Revenue and Code first (highest volatility). (Code/ops side done: `coo.sentinel-uptime` in `/sentinels` — homepage/sitemap/deploy checks, wakes CEO on anomaly, `python -m sentinels.watch`. Revenue sentinel awaits Search Console data.)
- [ ] Bring remaining departments (CRO, CFO, COO, Legal, Trading) online one at a time, same pilot-then-integrate pattern.
- [ ] Trading Desk: start with paper-trading/dry-run only until risk-manager caps are verified working, THEN go live with the 5,000 INR baseline.

## Phase 4 — Self-Evolution Activation (Month 4-6)

- [ ] Stand up RnD Hub's `oss-scout` running on a weekly cadence.
- [ ] Formalize Agent-Forge's sandbox -> shadow -> live pipeline; run it on at least 3 historical friction cases before trusting it live.
- [ ] Turn on department self-grading (05_SELF_EVOLUTION.md Growth Mechanism 3).
- [ ] Migrate memory from bootstrap SQLite to Postgres(+pgvector), then full Cognee vector+graph layer once volume/complexity justifies it.

## Phase 5 — Production Hardening (Month 6+)

- [ ] Full COO `launch-runbook` + `incident-postmortem` discipline enforced on every deploy.
- [ ] Weekly + monthly audit cadence (08_GOVERNANCE_AND_SAFETY.md) actually running, not just documented.
- [ ] Chairperson dashboard: single view of revenue delta, cost delta, open approvals, self-evolution log.
- [ ] Begin Stage 2 (Compound) of the scaling table in 05_SELF_EVOLUTION.md — Agent-Forge adding agents monthly, RnD Hub swapping in real cost savings.

## Success Metrics to Track From Day 1

| Metric | Why It Matters |
|---|---|
| Revenue delta per cycle | Prime Directive #1 |
| Cost per task (tokens + real spend) | Prime Directive #2 |
| DoD hit-rate per department | Quality control |
| Ledger entries requiring human approval vs total | Governance calibration |
| New agents graduated to live per month | Self-evolution velocity |
| Sentinel-triggered early cycles vs scheduled cycles | System responsiveness |

## First Command to Give Claude Code

"Read all files in /docs. Adopt the AI CEO persona from 00_MASTER_PROMPT.md. Phase 0 is complete — verify it (run tests, check kill switch), then begin Phase 1: build the CMO department's sub-agent roster in dry-run mode and report what's built and what's blocked."
