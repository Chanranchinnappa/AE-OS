# CLAUDE.md — Project Instructions for Claude Code

This file is read automatically by Claude Code at the start of every session in this repo. Keep it in the project root.

> NOTE: The live version of this file is `/CLAUDE.md` at the repo root, adapted for the current bootstrap phase (SQLite, near-zero budget, CMO pilot). This copy is the original template.

## Project

AE-OS: a self-evolving, multi-agent autonomous business operating system. Goal: production-ready, revenue-generating, cost-minimizing, self-improving software run largely without human intervention, with a human Chairperson holding final veto power.

## Repo Layout Convention

```
/ae-os
  /core           -> CEO orchestrator, loop scheduler, persona engine
  /departments
    /cmo /cro /cfo /cdo /coo /legal /trading
  /rnd-hub        -> open-source scouting + agent-forge
  /memory         -> Cognee/vector+graph wiring, Ephemera, Company Registry, Ledger
  /sentinels      -> always-on lightweight watchers per department
  /interfaces     -> chat/voice interface, Chairperson dashboard
  /docs           -> this documentation set (00-11 markdown files)
  /tests          -> unit + integration + agent-behavior tests
  /infra          -> deployment, CI/CD, secrets management
```

## Non-negotiable Coding Rules

- Every sub-agent is its own module with a single-responsibility system prompt file (`.md` or `.yaml`) stored alongside its code — never hardcode prompts inline in application logic.
- Every agent action must write a structured log entry to `/memory/ledger` before returning success.
- No agent may call a paid/premium LLM API without going through the `/core/model-router` which enforces the free-model-first policy from 07_TECH_STACK_AND_INFRA.md.
- All money-moving or production-deploying actions require a `requires_human_approval: true` flag and must halt for Chairperson sign-off — never auto-approve these.
- Write tests before or alongside every new sub-agent (TDD, per CDO's `superpowers` sub-agent).
- Never delete Ledger entries. Corrections are appended, never overwritten.
- Every PR/commit message must state: what changed, which department/agent owns it, and estimated cost/revenue impact.

## Definition of Done (applies repo-wide)

A task is only "done" when: code is tested, logged to the Ledger schema, documented in the relevant `/docs` file, reviewed by the CDO's QA gate, and — if it touches revenue or cost — verified by the CFO's `pricing-math` sub-agent.

## Session Startup Checklist for Claude Code

1. Read `/docs/00_MASTER_PROMPT.md` and adopt the AI CEO persona for this session unless told otherwise.
2. Check `/memory/ledger` for the most recent 10 entries to understand current state before acting.
3. Confirm which department/sub-agent this session is operating as.
4. If a structural change to architecture is requested, flag it for Chairperson approval before implementing.
5. If uncertain which sub-agent should own a task, consult `/docs/03_AGENT_SPECS.md` before creating a new one — do not duplicate responsibilities.

## Escalation Protocol

Stop and ask the Chairperson directly when: budget threshold exceeded, legal risk flagged, irreversible production action, or when two departments produce contradictory recommendations that the CEO cannot resolve algorithmically.
