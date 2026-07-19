"""CMO department — Phase 1 pilot (10_BUILD_ROADMAP.md).

Roster per 03_AGENT_SPECS.md: seo-audit, programmatic-seo, ai-seo,
cro-content, ad-creative, mktg-psychology.
"""
from .seo_audit import SeoAudit
from .programmatic_seo import ProgrammaticSeo
from .ai_seo import AiSeo
from .cro_content import CroContent
from .ad_creative import AdCreative
from .mktg_psychology import MktgPsychology
from .department import CMODepartment

ROSTER = (SeoAudit, ProgrammaticSeo, AiSeo, CroContent, AdCreative, MktgPsychology)
