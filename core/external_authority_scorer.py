"""
external_authority_scorer.py
Runs all external authority checks and returns ExternalAuthorityReport.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from .geo_checks import CheckResult
from .external_validator import ExternalValidationResult
from .external_authority_checks import (
    check_trustpilot_presence,
    check_clutch_g2_presence,
    check_linkedin_company,
    check_youtube_presence,
    check_crunchbase_presence,
    check_wikipedia_wikidata,
    check_knowledge_panel_signals,
    check_brand_directory_presence,
    check_google_business,
)


@dataclass
class ModuleScore:
    module: str
    score: int
    icon: str
    checks: List[CheckResult] = field(default_factory=list)


@dataclass
class ExternalAuthorityReport:
    external_authority: ModuleScore
    external_authority_score: int


def _mod_score(checks: List[CheckResult]) -> int:
    total = sum(c.score for c in checks)
    mx = sum(c.max_score for c in checks)
    return round(total / mx * 100) if mx else 0


def score(ext_validation: Optional[ExternalValidationResult] = None) -> ExternalAuthorityReport:
    """Run all external authority checks."""
    if ext_validation is None:
        # No external validation data — return empty report with zeroes
        placeholder = CheckResult(
            "External validation not run", 0, 1, "warn",
            "External profile validation was not performed (single-page mode).",
            "Enable full-site audit to validate external profiles.",
            "Re-run the audit with 'Full Site Audit' enabled for external validation.",
            effort="quick")
        mod = ModuleScore("External Authority", 0, "🌐", [placeholder])
        return ExternalAuthorityReport(external_authority=mod, external_authority_score=0)

    checks = [c for c in [
        check_trustpilot_presence(ext_validation),
        check_clutch_g2_presence(ext_validation),
        check_linkedin_company(ext_validation),
        check_youtube_presence(ext_validation),
        check_crunchbase_presence(ext_validation),
        check_wikipedia_wikidata(ext_validation),
        check_knowledge_panel_signals(ext_validation),
        check_brand_directory_presence(ext_validation),
        check_google_business(ext_validation),
    ] if c]

    mod = ModuleScore("External Authority", _mod_score(checks), "🌐", checks)
    return ExternalAuthorityReport(
        external_authority=mod,
        external_authority_score=mod.score,
    )
