# 05_SELF_EVOLUTION.md — How the System Grows Itself Over Years

## Philosophy

The system must get measurably better every week without waiting for the Chairperson to redesign it. Growth happens on three axes: **capability** (new sub-agents/skills), **efficiency** (lower cost per unit of output), and **judgment** (better decisions from accumulated Ledger history).

## Growth Mechanism 1 — Agent-Forge Pipeline

1. **Signal collection**: Agent-Forge continuously reads the Ledger for friction signatures — repeated manual escalations, tasks with no clear owning agent, tasks that took 3+ retries, or explicit Chairperson requests for a new capability.
2. **Proposal**: Agent-Forge drafts a new sub-agent spec (name, single job, inputs/outputs, DoD) using the same template as 03_AGENT_SPECS.md.
3. **Sandbox test**: The proposed agent runs in an isolated sandbox against historical replayed tasks from the Ledger before ever touching live data.
4. **Promotion**: If sandbox pass rate clears a defined threshold (e.g., 90% task success on replay), the agent goes live in shadow mode (runs alongside existing process, output logged but not acted on).
5. **Graduation**: After a defined number of shadow-mode cycles with acceptable accuracy, the agent goes fully live and 03_AGENT_SPECS.md is updated in the same commit.

## Growth Mechanism 2 — RnD Hub Cost/Capability Scouting

RnD Hub runs a standing scan (weekly minimum) against GitHub trending, HuggingFace new models, and relevant OSS project releases (targets named in the original brief: agent-routing frameworks, local knowledge-mapping tools, workflow-automation engines, memory-graph tools — treat these as example categories, not permanent brand commitments, since the OSS landscape moves fast). Every finding that could cut cost or add capability gets a one-page blueprint handed to CDO, tagged with estimated savings/benefit and integration effort.

## Growth Mechanism 3 — Department Self-Grading

At the end of every 24h cycle, each department scores itself against its own Definition of Done hit-rate over the trailing 7 and 30 days. A department whose hit-rate drops below threshold triggers an automatic COO `incident-postmortem`, not a punishment — a structured "why," feeding back into Agent-Forge as a signal.

## Growth Mechanism 4 — Prompt/Architecture Self-Patching

The CEO is explicitly permitted to rewrite sub-agent system prompts (not architecture) autonomously when it identifies a clear, low-risk improvement (e.g., an agent consistently misunderstands a field name). Anything touching architecture (adding/removing a department, changing reporting lines, changing budget authority) requires Chairperson sign-off per 08_GOVERNANCE_AND_SAFETY.md.

## Growth Mechanism 5 — Scaling the Human-Equivalent Team Over Years

| Stage | Approx. Timeline | Team Shape |
|---|---|---|
| Stage 0 — Bootstrap | Months 0-3 | CEO + 7 dept heads, minimal sub-agents, manual Chairperson review every cycle |
| Stage 1 — Stabilize | Months 3-9 | Full sub-agent rosters live, Sentinels operational, Ledger mature |
| Stage 2 — Compound | Year 1-2 | Agent-Forge actively adding new agents monthly; RnD Hub swaps in 2-3 cost-saving tools |
| Stage 3 — Multiply | Year 2-4 | New departments spun up only with Chairperson approval (e.g., a dedicated International Expansion desk); shadow-mode graduation rate becomes a tracked KPI |
| Stage 4 — Mature Enterprise | Year 4+ | System manages multiple simultaneous ventures/products under one Shared Memory; Chairperson reviews strategy, not operations |

## Hard Rule on "Push Itself to Its Hardest Limits"

Aggressiveness applies to effort and iteration speed, never to safety constraints. The system should retry, test more variants, and explore more revenue avenues than a human team would — but it must never bypass the approval gates in 08_GOVERNANCE_AND_SAFETY.md to "move faster." Speed comes from parallelizing sub-agents and shadow-mode testing, not from skipping verification.
