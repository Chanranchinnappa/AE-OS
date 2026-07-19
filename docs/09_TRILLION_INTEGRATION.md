# 09_TRILLION_INTEGRATION.md — What We Borrow from Trillion, and Why

## What Trillion Is

A pre-launch, voice-first "AI co-founder" product from an indie founder. It continuously watches six business systems (revenue, code, customers, data, comms, intel) via named single-purpose sub-agents, and communicates findings in short, direct, opinionated language rather than dashboard-speak. As of this writing it is signup-gated with no public code released yet — we are borrowing its concepts, not its codebase.

## Concept 1 — Persona-First Communication Layer

**What Trillion does**: replies like a sharp co-founder, not a report generator — brief, evidence-based, willing to state an opinion.
**How we implement it**: the Voice/Chat Interface (02_ARCHITECTURE.md, Layer 1) wraps every CEO output. Enforce via a fixed style directive in the CEO's system prompt (00_MASTER_PROMPT.md) — max length, mandatory "recommended next action" close, no hedging language.

## Concept 2 — Named, Single-Job Sub-Agents

**What Trillion does**: Flux, Relay, Scout, Prism, Atlas, Spark, Forge, Lift — each agent has one crisp job, which is more legible to a human founder than a bullet list.
**How we implement it**: keep our functional naming (e.g., `retention-guard`, `product-walkthrough`) but optionally give each sub-agent a short callsign in the interface layer only, for human legibility, without changing the underlying spec format in 03_AGENT_SPECS.md.

## Concept 3 — Dedicated Retention Agent (Lift)

**Gap it exposed**: our original CRO department only had `funnel-analytics` (drop-off detection), nothing proactively watching existing accounts for churn risk.
**Implementation**: `retention-guard` sub-agent added under CRO (see 03_AGENT_SPECS.md) — runs continuously, not just during funnel review, and produces a risk score + reason + suggested save-action per at-risk account.

## Concept 4 — Dedicated Meta-Agent (Forge)

**Gap it exposed**: our CEO informally "creates sub-agents" as a side task, with no auditable process.
**Implementation**: Agent-Forge formalized under RnD Hub (02_ARCHITECTURE.md section 7, 05_SELF_EVOLUTION.md Growth Mechanism 1) with a defined sandbox -> shadow -> live pipeline and a mandatory spec-file update on graduation.

## Concept 5 — Always-On Watching vs. Fixed-Interval Loops

**Gap it exposed**: our original design only ran on a 24-hour loop; Trillion frames itself as watching continuously.
**Implementation**: Sentinel Layer (02_ARCHITECTURE.md section 6) — lightweight, cheap, rule-based watchers per department that can trigger an early partial loop on anomaly, without running full expensive cycles constantly.

## Concept 6 — Cited Research, Not Link Dumps

**What Trillion's Atlas does**: hands back a cited brief instead of a pile of links.
**Implementation**: mandatory citation discipline added to CMO's `ai-seo` and RnD Hub's `oss-scout` — no research output ships without sourced claims (03_AGENT_SPECS.md DoD entries).

## Concept 7 — Live Product Dogfooding (Scout)

**Gap it exposed**: our `webapp-testing` is CI/pipeline-focused, not "walk the product like a real user."
**Implementation**: `product-walkthrough` sub-agent added under CDO, complementing rather than replacing CI testing.

## What We Deliberately Do NOT Copy

- Trillion is a single product monitoring one company's systems; AE-OS is a full enterprise OS that can eventually run multiple ventures — we keep our departmental depth (Legal, Trading, CFO modeling) rather than collapsing to 6 generic "systems."
- We do not adopt voice-first as the primary interface immediately — text/log-first with voice as a later add-on, since production readiness matters more than interface polish at this stage.
- We do not copy any of Trillion's actual code (none is public) — this file documents conceptual inspiration only, consistent with not reproducing another product's proprietary implementation.
