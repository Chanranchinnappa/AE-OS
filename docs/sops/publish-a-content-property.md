# SOP: Publish a content property

- **Version**: 1
- **Updated**: 2026-07-19
- **Owner**: coo.sop-builder
- **Originating Ledger entries**: `b32f1771-b1ac-468b-80a2-41f169a8d6ab`, `24d0ca9d-1b9e-427e-b394-ada40e82a9af`, `125ac850-fd14-4c10-a668-ea972c416ebc`, `f95d9aca-d28f-4fda-a492-11443364fbb9`

## Steps

1. Register the property in config/settings.json venture.properties (status in_build)
2. Scaffold pages under sites/<name>/ — every claim sourced or mechanism-based
3. Run cmo.seo-audit via the CEO cycle; apply every scored fix
4. Re-audit until the scan reports zero issues
5. Generate supporting pages with cmo.programmatic-seo; only truthfulness-gated drafts leave drafts/
6. Run coo.launch-runbook: preflight + rollback plan + production_deploy approval request
7. Halt until the Chairperson decides via python -m core.approval_gate
