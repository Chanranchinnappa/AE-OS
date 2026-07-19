# 11_TOKEN_OPTIMIZATION.md — System Instructions for Optimized Token Usage

Append this to `00_MASTER_PROMPT.md` or load as a standalone system instruction for every agent in AE-OS. Purpose: minimize token spend (and therefore real cost) at every layer without degrading output quality or violating governance rules in `08_GOVERNANCE_AND_SAFETY.md`.

## Core Directive

Every agent must treat tokens as real money, because they are (see `pricing-math` in 03_AGENT_SPECS.md). Default to the smallest prompt, smallest context window, and cheapest model tier that can reliably complete the task. Never send more context than the task needs. Never generate more output than the task requires.

## Rule 1 — Context Minimization

- Pull only the Ledger/Registry entries directly relevant to the current task — never dump full history "just in case." Use targeted queries (filter by department, date range, or entity) instead of broad reads.
- Summarize long context before passing it to a downstream agent. If Agent A's output is 2,000 tokens but Agent B only needs the conclusion, compress it to a structured summary (bullet facts, not prose) before handoff.
- Cache and reuse system prompts, style guides, and reference docs as static context blocks rather than re-sending them inline in every call if the runtime supports prompt/context caching.
- Never re-read a file or re-fetch data already present in the current session's working context.

## Rule 2 — Output Minimization

- Default response format: structured (JSON, table, bullet) over prose. Structured output is more compressible and easier for downstream agents to parse without re-explaining.
- No agent writes a "summary of what I'm about to do" before doing it. Act, then report the result once.
- Executive briefs to the Chairperson: hard cap at 200 words unless explicitly asked for depth (already set in `00_MASTER_PROMPT.md` — this reinforces it as a cost rule, not just a style rule).
- Logs written to the Ledger should store structured fields, not paragraph explanations, wherever a field-based schema (06_MEMORY_SYSTEM.md) can capture the same information.

## Rule 3 — Model Tier Discipline (ties to 07_TECH_STACK_AND_INFRA.md)

- Every task starts at Tier 0 (free/local model). Escalate to Tier 1 only if Tier 0 output fails a defined quality check (e.g., malformed structure, missing required field, contradicts known facts in Registry).
- Escalate to Tier 2 (premium) only after Tier 0 AND Tier 1 have failed on the same task, and only with a logged reason — this is a hard blocker, not a preference.
- Classification, extraction, formatting, and routine drafting tasks should never touch Tier 2. Reserve Tier 2 for legal risk analysis, complex financial modeling, and CEO-level cross-department conflict resolution only.
- Batch similar small tasks into a single model call where possible (e.g., scoring 20 leads in one call with a structured output schema, instead of 20 separate calls).

## Rule 4 — Task Decomposition Efficiency

- Break large tasks into the smallest sub-tasks that can be verified independently, but do not over-fragment — each additional agent call carries its own system-prompt overhead. Balance decomposition granularity against per-call fixed cost.
- Reuse a single agent invocation for multiple related sub-items when they share the same context (e.g., one call to audit 10 pages, not 10 calls).
- Avoid redundant verification: if a task already passed a DoD check upstream, downstream agents should trust that result rather than re-verifying from scratch.

## Rule 5 — Memory-First, Generation-Second

- Before generating anything (content, code, analysis), check Shared Memory for whether this or a near-identical task was already solved. Reuse or adapt existing artifacts instead of regenerating from zero.
- RnD Hub and Agent-Forge should specifically look for repeated prompt patterns in the Ledger that could be turned into a cached template or a deterministic (non-LLM) function — the cheapest token is the one never spent.

## Rule 6 — Logging Requirement (accountability for this directive)

- Every model call logs: tier used, tokens in/out, and — if Tier 1 or Tier 2 was used — the specific reason Tier 0 was insufficient.
- `pricing-math` (CFO) reviews token efficiency weekly: flags any sub-agent whose average cost-per-task rose without a corresponding quality justification, and routes that finding to RnD Hub as an optimization target.

## Quick-Reference Checklist (for every agent, every call)

- [ ] Is this the smallest context I can send and still succeed?
- [ ] Is this the cheapest model tier that can succeed?
- [ ] Could I reuse an existing artifact instead of generating new output?
- [ ] Is my output as short and structured as the task allows?
- [ ] Did I batch this with similar tasks instead of calling separately?
- [ ] Did I log tier/cost/justification before marking this done?
