"""
crawlability_scorer.py
Runs Section 1 (Technical AI Crawlability) + Section 2 (Schema Markup Depth).
Returns CrawlabilityReport with two ModuleScore objects.
"""
from dataclasses import dataclass, field
from typing import List
from .geo_checks import CheckResult
from .crawlability_checks import (
    check_llms_txt, check_ai_bot_directives, check_page_render_type, check_ttfb,
    check_organization_schema, check_service_schema, check_author_schema,
    check_breadcrumb_schema, check_howto_article_schema, check_schema_validation,
)


@dataclass
class ModuleScore:
    module: str
    score: int
    icon: str
    checks: List[CheckResult] = field(default_factory=list)


@dataclass
class CrawlabilityReport:
    crawlability: ModuleScore
    schema_depth: ModuleScore
    crawlability_score: int   # avg of both (used for weighted overall)
    schema_score: int


def _mod_score(checks: List[CheckResult]) -> int:
    total = sum(c.score for c in checks)
    mx = sum(c.max_score for c in checks)
    return round(total / mx * 100) if mx else 0


def score(page) -> CrawlabilityReport:
    # Section 1 — Technical AI Crawlability
    crawl_checks = [c for c in [
        check_llms_txt(page),
        check_ai_bot_directives(page),
        check_page_render_type(page),
        check_ttfb(page),
    ] if c]
    crawl = ModuleScore("Technical AI Crawlability", _mod_score(crawl_checks), "🕷️", crawl_checks)

    # Section 2 — Schema Markup Depth
    schema_checks = [c for c in [
        check_organization_schema(page),
        check_service_schema(page),
        check_author_schema(page),
        check_breadcrumb_schema(page),
        check_howto_article_schema(page),
        check_schema_validation(page),
    ] if c]
    schema = ModuleScore("Schema Markup Depth", _mod_score(schema_checks), "🗂️", schema_checks)

    return CrawlabilityReport(
        crawlability=crawl,
        schema_depth=schema,
        crawlability_score=crawl.score,
        schema_score=schema.score,
    )
