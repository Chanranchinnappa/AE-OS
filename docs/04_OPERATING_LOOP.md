# 04_OPERATING_LOOP.md — The Daily Execution Cycle

## Purpose

Defines exactly what happens every cycle, in what order, with what guardrails. This is the literal runtime loop the CEO orchestrator executes.

## Trigger Conditions

- Scheduled: every 24 hours by default (configurable per department).
- Event-triggered: any Sentinel firing an anomaly (see 02_ARCHITECTURE.md section 6) starts an early partial-loop for the affected department(s) only.
- Manual: Chairperson can trigger a full or partial loop on demand via the interface.

## Step-by-Step

### Step 1 — Ingestion
CEO queries Shared Memory: last cycle's Ledger entries, current Company Registry state, any open Sentinel alerts, any pending Chairperson approvals. Output: a state snapshot object.

### Step 2 — Task Allocation
CEO diffs the state snapshot against standing goals (revenue targets, OpEx ceiling, active projects). Produces a task list per department, each tagged with priority (P0 = revenue-blocking, P1 = growth, P2 = maintenance/self-evolution).

### Step 3 — Autonomous Iteration
Each department's sub-agents execute inside isolated workspaces. Sub-agents may call each other's outputs via Shared Memory reads but may not directly invoke another department's execution — cross-department requests go back through the CEO's task queue.

### Step 4 — Verification (new vs. original)
Before any output is logged as complete, it passes the department's Definition of Done (03_AGENT_SPECS.md). CDO outputs additionally pass `webapp-testing`. Financial outputs pass `pricing-math` reconciliation. Legal-sensitive outputs pass `compliance`.

### Step 5 — Logging
Every action writes to the Ledger: timestamp, agent ID, action taken, cost incurred (tokens + any real spend), result, links to any artifacts produced. No silent actions.

### Step 6 — RnD Review
RnD Hub scans the day's Ledger for repeated expensive operations and proposes open-source substitutions. Agent-Forge reviews friction logs (tasks that took multiple retries, ambiguous ownership, or missing capability) and proposes new/modified sub-agents.

### Step 7 — Compilation & Synthesis
CEO aggregates: Revenue Impacts Made, Operational Improvements Attempted, System Cost Reductions Unlocked, Self-Evolution Proposals, Items Needing Chairperson Approval. Formats into the persona-wrapped executive brief (Layer 1).

### Step 8 — Chairperson Checkpoint
If anything in the brief is tagged `requires_human_approval`, the loop pauses on that item specifically (other items still ship) until the Chairperson responds.

## Loop Timing Budget (starting point, tune later)

| Phase | Target Duration |
|---|---|
| Ingestion | < 2 min |
| Allocation | < 3 min |
| Iteration | Bulk of cycle, department-dependent |
| Verification | Continuous, per-output |
| Logging | Real-time, not batched |
| RnD Review | Once per full 24h cycle |
| Compilation | < 5 min |

## Failure Handling

If a department fails to complete its P0 tasks by cycle end, COO's `incident-postmortem` runs automatically, and the CEO carries the task forward with a flag, never silently drops it.
