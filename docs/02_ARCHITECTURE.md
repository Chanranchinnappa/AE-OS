# 02_ARCHITECTURE.md — Full System Architecture

## 1. Layered Overview

```
Layer 0: CHAIRPERSON            -> human, final veto, budget owner
Layer 1: VOICE/CHAT INTERFACE    -> persona-wrapped I/O (Trillion-style brevity)
Layer 2: AI CEO                  -> orchestration, strategy, self-modification
Layer 3: DEPARTMENTS (7)         -> CMO, CRO, CFO, CDO, COO, Legal, Trading
Layer 4: SUB-AGENTS (30+)        -> single-responsibility workers per department
Layer 5: SENTINEL LAYER          -> always-on lightweight anomaly watchers
Layer 6: RND HUB + AGENT-FORGE   -> capability growth, cost-reduction scouting
Layer 7: SHARED MEMORY           -> Ephemera / Company Registry / Ledger (Cognee)
Layer 8: INFRA & MODEL ROUTER    -> compute, model selection, secrets, deployment
```

Data flows downward as tasks, upward as logs/results, and laterally through Shared Memory so any agent can query any other department's state without a direct call.

## 2. The Chairperson

Sole holder of veto power and budget authority. Interacts only through the Voice/Chat Interface. Receives one compiled report per cycle plus real-time alerts for anything requiring sign-off (see 08_GOVERNANCE_AND_SAFETY.md for exact triggers).

## 3. Voice/Chat Interface

Wraps every CEO output in a fixed persona: brief, evidence-cited, opinionated, always ends in a recommended action. Supports text-first with optional TTS/voice mode later. Never lets a department talk directly to the Chairperson — everything routes through the CEO for synthesis.

## 4. The AI CEO

Responsibilities: goal decomposition, cross-department task allocation, conflict resolution between departments, self-modification of agent prompts/architecture, escalation gatekeeping. The CEO owns the Operating Loop defined in 00_MASTER_PROMPT.md. It is the only node permitted to spawn or retire a department; sub-agent creation within a department is delegated to Agent-Forge.

## 5. Departments and Reporting Lines

| Department | Reports To | Owns Budget For | Key Output |
|---|---|---|---|
| CMO | AI CEO | Ad spend, content tooling | Traffic, conversion lift |
| CRO | AI CEO | Sales tooling, lead data | Revenue pipeline, retention |
| CFO | AI CEO | Financial tooling | Live financial statements, runway |
| CDO | AI CEO | Dev tooling, infra | Shipped, tested product |
| COO | AI CEO | Ops tooling | SOPs, uptime, incident reports |
| Legal | AI CEO | Legal/compliance tooling | Risk clearance |
| Trading | AI CEO | Trading capital (ring-fenced) | Signals, P&L |

Full sub-agent rosters for each are defined in 03_AGENT_SPECS.md.

## 6. Sentinel Layer (new vs. original design)

A thin always-on process per department, cheap enough to run continuously (small/free models, rule-based thresholds, or simple statistical checks), whose only job is to detect anomalies and fire an early Operating Loop cycle instead of waiting for the fixed schedule. Examples: revenue drop >10% day-over-day, failed deploy, churn spike, a legal filing deadline, a trading stop-loss breach. Sentinels never take action themselves — they only wake the relevant department + CEO.

## 7. RnD Hub + Agent-Forge

RnD Hub scouts GitHub/HuggingFace/open-source ecosystems for tools that cut token/API costs or add capability, and hands a technical deployment blueprint to the CDO. Agent-Forge (a formal sub-unit of RnD Hub) is the only entity permitted to design, test, and deploy brand-new sub-agents — this is how the "team grows over the years" without the CEO hand-rolling every new hire. See 05_SELF_EVOLUTION.md.

## 8. Shared Memory

Three tiers, all backed by a vector + graph database (Cognee or equivalent):

- **Ephemera** — short-term session context, cleared/archived after each cycle.
- **Company Registry** — current-state truth: codebase state, API keys (via secrets manager, never raw in registry), business logic, active metrics.
- **The Ledger** — append-only historical log of every action, asset, failure, and financial change. Nothing is ever deleted from the Ledger; corrections are new entries referencing the old one.

## 9. Infra & Model Router

Sits underneath everything. Routes every LLM call through a policy: default to free/open-source (self-hosted Ollama nodes or free-tier hosted models), escalate to premium models only on a logged hard blocker (see 07_TECH_STACK_AND_INFRA.md for exact routing table). Owns deployment pipelines, secrets, and observability.

## 10. Failure Isolation Principle

Every department runs in an isolated execution workspace (separate process/container/sandbox). A crash or runaway loop in one department must never take down another department or the CEO. Sentinels and the CEO's own heartbeat check enforce this.
