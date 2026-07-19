# Sentinel Spec — coo.sentinel-uptime

Single job: continuously verify that live venture properties are reachable
(homepage, sitemap, every sitemap URL) and that their last deploy succeeded.

Rules (02_ARCHITECTURE.md §6, 06_MEMORY_SYSTEM.md access rules):
- Rule-based only — no LLM calls, ever. A sentinel that spends tokens is
  doing someone else's job.
- Read-only, except the single alert record it logs per watch run.
- NEVER remediates. On anomaly it wakes the CEO for an early partial cycle
  (and routes to COO incident-postmortem once built). Detection and action
  are different jobs owned by different layers.
- Respects the kill switch like every other component.
