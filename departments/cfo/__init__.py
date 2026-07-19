"""CFO department — Phase 2 second department (10_BUILD_ROADMAP.md).

Bootstrap roster: pricing-math only (repo-wide DoD depends on it). Remaining
CFO agents (dcf-model, 3-statements, lbo-model, comps-analysis) arrive with
real revenue data in Phase 3.
"""
from .pricing_math import PricingMath

ROSTER = (PricingMath,)
