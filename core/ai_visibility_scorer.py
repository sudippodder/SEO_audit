"""
ai_visibility_scorer.py
Runs AI visibility checks (heuristic + live OpenAI tests) and returns AIVisibilityReport.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from .geo_checks import CheckResult
from .external_validator import ExternalValidationResult
from .ai_tester import AITestResult
from .ai_visibility_checks import (
    check_ai_bot_access_readiness,
    check_schema_ai_readiness,
    check_content_citation_readiness,
    check_external_authority_for_ai,
    check_entity_recognition_readiness,
    # Live AI test checks
    check_ai_brand_recognition,
    check_ai_keyword_ranking,
    check_ai_sentiment,
    check_ai_competitor_landscape,
)


@dataclass
class ModuleScore:
    module: str
    score: int
    icon: str
    checks: List[CheckResult] = field(default_factory=list)


@dataclass
class AIVisibilityReport:
    ai_visibility: ModuleScore
    ai_visibility_score: int
    ai_test_result: Optional[AITestResult] = None


def _mod_score(checks: List[CheckResult]) -> int:
    total = sum(c.score for c in checks)
    mx = sum(c.max_score for c in checks)
    return round(total / mx * 100) if mx else 0


def score(
    page,
    ext_validation: Optional[ExternalValidationResult] = None,
    ai_test: Optional[AITestResult] = None,
) -> AIVisibilityReport:
    """Run all AI visibility checks (heuristic + live tests if available)."""
    # Heuristic checks (always run)
    checks = [c for c in [
        check_ai_bot_access_readiness(page),
        check_schema_ai_readiness(page),
        check_content_citation_readiness(page),
        check_external_authority_for_ai(ext_validation),
        check_entity_recognition_readiness(page, ext_validation),
    ] if c]

    # Live AI test checks (only run if ai_test data is available)
    if ai_test and ai_test.tested:
        live_checks = [c for c in [
            check_ai_brand_recognition(ai_test),
            check_ai_keyword_ranking(ai_test),
            check_ai_sentiment(ai_test),
            check_ai_competitor_landscape(ai_test),
        ] if c]
        checks.extend(live_checks)

    mod = ModuleScore("AI Visibility", _mod_score(checks), "🤖", checks)
    return AIVisibilityReport(
        ai_visibility=mod,
        ai_visibility_score=mod.score,
        ai_test_result=ai_test,
    )
