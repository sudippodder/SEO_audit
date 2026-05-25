"""
content_quality_scorer.py
Runs Section 6 (Content Quality & LLM Readability) + Section 7 (Off-Page Authority heuristic).
Returns ContentQualityReport with two ModuleScore objects.
"""
from dataclasses import dataclass, field
from typing import List
from .geo_checks import CheckResult
from .content_quality_checks import (
    check_statistics_density, check_quotable_sentences, check_content_freshness,
    check_reading_clarity, check_conversational_match, check_semantic_coverage,
    check_author_credibility, check_source_citations,
    check_social_profile_links, check_review_platform_links, check_press_mentions,
)


@dataclass
class ModuleScore:
    module: str
    score: int
    icon: str
    checks: List[CheckResult] = field(default_factory=list)


@dataclass
class ContentQualityReport:
    content_quality: ModuleScore
    off_page: ModuleScore
    content_quality_score: int
    off_page_score: int


def _mod_score(checks):
    total = sum(c.score for c in checks)
    mx = sum(c.max_score for c in checks)
    return round(total / mx * 100) if mx else 0


def score(page, kw: str = "") -> ContentQualityReport:
    # Section 6 + Section 5 gaps
    cq_checks = [c for c in [
        check_statistics_density(page),
        check_quotable_sentences(page),
        check_content_freshness(page),
        check_reading_clarity(page),
        check_conversational_match(page),
        check_semantic_coverage(page, kw),
        check_author_credibility(page),
        check_source_citations(page),
    ] if c]
    cq = ModuleScore("Content Quality & LLM Readability", _mod_score(cq_checks), "📖", cq_checks)

    # Section 7 — Off-Page Authority (heuristic)
    op_checks = [c for c in [
        check_social_profile_links(page),
        check_review_platform_links(page),
        check_press_mentions(page),
    ] if c]
    op = ModuleScore("Off-Page & Citation Authority", _mod_score(op_checks), "🔗", op_checks)

    return ContentQualityReport(
        content_quality=cq,
        off_page=op,
        content_quality_score=cq.score,
        off_page_score=op.score,
    )
