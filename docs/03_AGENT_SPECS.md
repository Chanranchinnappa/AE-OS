# 03_AGENT_SPECS.md — Full Sub-Agent Roster & Definitions of Done

Format for every sub-agent: **Name | Department | Single Job | Inputs | Outputs | Definition of Done | Escalation Trigger**

## CMO — Chief Marketing Officer

| Agent | Job | DoD |
|---|---|---|
| seo-audit | Continuous on-page/technical SEO scans | Report with scored issues + fixes, logged to Ledger |
| programmatic-seo | Mass-builds data-driven landing pages | Pages pass QA — incl. truthfulness gate: no seller-voice, no numeric claims absent from source data — indexed check scheduled |
| ai-seo | Optimizes content to rank in AI engine summaries (with citation discipline) | Content cites real sources, no hallucinated claims; draft passes shared truthfulness gate (no seller-voice, no unsourced numbers) |
| cro-content (funnel-facing content, distinct from CRO dept) | Multi-variable on-page conversion tests | Test has control, variant, sample-size check |
| ad-creative | Scales ad graphic/text variants | Each variant tagged with hypothesis being tested |
| mktg-psychology | Behavioral trigger analysis for messaging | Recommendation backed by data, not just theory |

## CRO — Chief Revenue Officer

| Agent | Job | DoD |
|---|---|---|
| lead-generation | Scrapes/scores high-intent leads | Leads deduped, scored, written to Registry |
| pricing-optimizer | A/B tests pricing/tiers/currency | Test has defined success metric + duration |
| funnel-analytics | Monitors funnel drop-off | Drop-off point identified with % and next test proposed |
| partnership-scout | Finds affiliate/white-label partners | Candidate list vetted against Legal's compliance flags |
| **retention-guard** (new) | Proactively flags at-risk accounts before churn | Risk score + reason + suggested save-action logged |

## CFO — Chief Financial Officer

| Agent | Job | DoD |
|---|---|---|
| dcf-model | Continuous DCF valuation | Model reconciles to latest actuals, assumptions logged |
| 3-statements | Live Balance Sheet/Income/Cash Flow | Statements balance, reconciled daily |
| lbo-model | LBO/acquisition math for micro-SaaS targets | Sensitivity table included |
| comps-analysis | Benchmarks vs industry SaaS multiples | Comp set justified, sourced |
| pricing-math | Granular COGS incl. exact API token cost per execution | Cost-per-task figure updated after every model-router change |

## CDO — Chief Development Officer

| Agent | Job | DoD |
|---|---|---|
| superpowers | Architecture planning, system design, TDD | Tests written before/with code, design doc logged |
| context-puller | Pulls version-exact live docs for frameworks | No hallucinated API usage; doc source cited |
| mcp-builder | Builds MCP servers bridging OS to external systems | Server passes integration test |
| skill-creator | Generates new modular skills/scripts | Skill has its own spec file + test |
| webapp-testing | Headless-browser CI testing | Green pipeline before merge |
| **product-walkthrough** (new) | Walks live product end-to-end like a real user | Bug/friction report with repro steps |

## COO — Chief Operations Officer

| Agent | Job | DoD |
|---|---|---|
| sop-builder | Codifies repeatable actions into SOPs | SOP versioned, linked to originating logs |
| incident-postmortem | Blameless review on failures | Root cause + prevention action logged |
| business-case | ROI estimate before CDO builds a feature | Case includes cost, expected revenue, breakeven point |
| launch-runbook | Controls deploys, versioning, infra security | Rollback plan documented before every deploy |
| internal-comms | Cross-department briefs to cut redundant work | Brief distributed before next cycle starts |

## Legal Desk

| Agent | Job | DoD |
|---|---|---|
| contract-review | Clause-by-clause TOS/license scans | Risk flags categorized by severity |
| nda-triage | Auto-triages incoming NDAs | Unfavorable terms flagged with suggested redline |
| compliance | Cross-border regulatory checks | Jurisdiction-specific checklist completed |
| loophole-registry | Corporate registry/tax jurisdiction research | Findings cited, legality double-checked |

## Trading & Analytics Desk

| Agent | Job | DoD |
|---|---|---|
| market-analyzer | Parses charts, order flow, macro news | Analysis timestamped, sources logged |
| signal-generator | Outputs BUY/SELL/HOLD w/ entry, stop-loss, target | Signal includes risk/reward ratio |
| risk-manager | Caps exploration trades at defined baseline, scales only after verified profitable sprint | No trade executes above the current approved cap |

## RnD Hub

| Agent | Job | DoD |
|---|---|---|
| oss-scout | Scours GitHub/HuggingFace for cost-cutting tools | Blueprint handed to CDO with cost-savings estimate |
| **agent-forge** (new, formalized) | Designs/tests/deploys new sub-agents | New agent has spec entry in this file + passing test before going live |

## Cross-Cutting Rule

No sub-agent may be created outside Agent-Forge's process. Every new agent added to the roster must update this file in the same commit that ships its code.
