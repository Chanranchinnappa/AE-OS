"""COO department — Phase 2 third department (10_BUILD_ROADMAP.md).

Bootstrap roster: sop-builder + launch-runbook (the deploy gate brightpaths
must pass). Remaining COO agents (incident-postmortem, business-case,
internal-comms) arrive in Phase 3.
"""
from .sop_builder import SopBuilder
from .launch_runbook import LaunchRunbook

ROSTER = (SopBuilder, LaunchRunbook)
