# 07_TECH_STACK_AND_INFRA.md — Technology Choices and Model Routing

## Guiding Principle

Default to free/open-source; escalate to paid only on a logged, justified blocker. Every escalation must be recorded with a reason in the Ledger so cost creep is visible, not silent.

## Model Router Policy

| Tier | When Used | Example Models |
|---|---|---|
| Tier 0 — Local/Free | Default for all routine sub-agent tasks (classification, drafting, summarization) | Self-hosted Ollama nodes, free-tier open models (e.g., Llama-family, DeepSeek-family, Nemotron-family — pick current best-available free/open checkpoint at deploy time, do not hardcode a specific version long-term) |
| Tier 1 — Mid-tier free/cheap API | Tasks needing longer context or better reasoning but not mission-critical | Free-tier hosted APIs with rate limits |
| Tier 2 — Premium | Only on a CEO-logged hard blocker (Tier 0/1 failed twice on the same task, or task is high-stakes: legal, financial modeling, production deploy decision) | Premium hosted frontier models |

Every model call is logged with: model used, tokens in/out, cost, and tier justification if Tier 2.

> BOOTSTRAP STATUS: implemented in `/core/model_router.py` (Phase 0), Tier 0 = dry-run provider until Ollama is installed.

## Recommended Stack (bootstrap-friendly, production-capable)

- **Orchestration runtime**: Claude Code / OpenCode AI for agentic dev + execution, since you already use these.
- **Sub-agent framework**: lightweight agent framework (e.g., LangGraph, CrewAI, or a hand-rolled task-queue) — pick whichever has the least lock-in; the architecture in 02_ARCHITECTURE.md must not depend on one vendor's SDK.
- **Memory**: per 06_MEMORY_SYSTEM.md — Postgres (+pgvector) as the pragmatic bootstrap choice, Cognee layered in once volume justifies it. (Bootstrap-of-the-bootstrap: SQLite, currently live.)
- **Workflow automation**: your existing Google Sheets/Apps Script stack for lightweight internal tooling; graduate hot paths to proper backend services as load grows.
- **Deployment**: containerized services (Docker) behind a simple CI/CD (GitHub Actions), one environment for staging, one for production, gated by COO's `launch-runbook`.
- **Secrets**: a dedicated secrets manager (never in the Company Registry or in code) — e.g., cloud provider's native secrets manager or a self-hosted Vault.
- **Observability**: structured logs feeding the Ledger + a lightweight metrics dashboard (Looker Studio, since you already use it, or Grafana if self-hosting).

## RnD Hub's OSS Scouting Targets (treat as starting examples, refresh regularly)

Agent-routing frameworks, local knowledge-mapping/visual tools, workflow-automation engines, memory-graph frameworks. RnD Hub's job is to keep re-evaluating this list — it will be stale within months given how fast the OSS agent ecosystem moves.

## Cost Discipline

CFO's `pricing-math` sub-agent must be able to answer, for any single task type: "what did this cost in tokens and real currency, and what would it cost if we downgraded to Tier 0." This number feeds every RnD Hub cost-reduction proposal.
