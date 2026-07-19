# 06_MEMORY_SYSTEM.md — Shared Vector/Graph Memory Layer

## Purpose

One unified memory substrate every agent reads from and writes to, so context is never siloed inside a single conversation or department.

## Recommended Implementation (production-ready path)

- **Vector store**: start with a managed/open-source vector DB (e.g., Qdrant, Weaviate, or pgvector on Postgres) for embeddings-based recall — cheap and battle-tested.
- **Graph layer**: Cognee (or a comparable open-source memory-graph framework) on top, for relationship modeling (which agent produced which artifact, which decision depended on which fact).
- **Source of truth for structured data**: a normal relational DB (Postgres/SQLite for bootstrap) for the Ledger and Company Registry — do not force structured financial/operational data into a vector store just because it's trendy.

> BOOTSTRAP STATUS: implemented as SQLite in `/memory/db.py` (Phase 0). Vector/graph layers arrive in Phase 4.

## Three-Tier Data Model

### Tier 1 — Ephemera
Short-term, per-session working context (current task, current sub-agent scratchpad). TTL-based expiry (e.g., 24-72 hours), archived to Ledger summaries before deletion, never silently lost.

### Tier 2 — Company Registry
Current-state truth: codebase state/version, active API integrations (references to secrets, never raw secrets), business logic rules, live metrics snapshots, department rosters. Overwritten in place as state changes, but every overwrite is mirrored to the Ledger as a diff.

### Tier 3 — The Ledger
Append-only, immutable. Every entry contains: timestamp, department, agent ID, action type, inputs, outputs/artifacts, cost (tokens + real currency), result status, and links to any Chairperson approvals involved. This is the system's institutional memory and audit trail — it is what Agent-Forge, RnD Hub, and self-grading all read from.

## Schema Sketch (Ledger table, minimum viable)

| Field | Type | Notes |
|---|---|---|
| id | UUID | primary key |
| timestamp | datetime | UTC |
| department | string | enum: CMO/CRO/CFO/CDO/COO/Legal/Trading/RnD |
| agent_id | string | e.g., "cro.retention-guard" |
| action_type | string | e.g., "flag_at_risk_account" |
| inputs | JSON | |
| outputs | JSON | includes artifact links |
| cost_tokens | int | |
| cost_currency | decimal | real spend if any |
| status | enum | success / failed / needs_approval |
| approval_ref | UUID nullable | links to Chairperson decision record |

## Access Rules

- Any agent can READ any tier for context.
- Only the owning department can WRITE to its own Company Registry section.
- Only the logging middleware (never an agent directly) writes to the Ledger, guaranteeing consistent schema and preventing tampering.
- Sentinels read-only; they never write except their own alert record.

## Retrieval Pattern

Every agent, before acting, runs a context pull: relevant Ledger history (last N related entries) + relevant Registry state + any Ephemera scratch from the current session. This is what prevents duplicate work and hallucinated context.
