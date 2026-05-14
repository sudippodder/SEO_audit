"""
geo_scorer.py
Runs all 7 GEO / AI-focused scoring modules using geo_checks.py.
Returns a GeoReport dataclass consumed by audit_engine and app.py.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from .geo_checks import (
    CheckResult,
    # Module 1 – AI Citation Readiness
    check_service_definitions, check_faq_for_citation, check_summary_for_citation,
    check_structured_formatting, check_extractable_answers,
    # Module 2 – Brand / Entity Clarity
    check_business_clarity, check_services_listed, check_industry_category, check_brand_consistency,
    # Module 3 – AI Extractability
    check_short_answer_paragraphs, check_definition_content, check_structured_lists,
    check_scannable_formatting, check_comparison_content,
    # Module 4 – AI Trust Signals
    check_testimonials, check_case_studies, check_about_team,
    check_trust_badges, check_contact_transparency,
    # Module 5 – AI Overview Readiness
    check_qa_formatting, check_informational_structure, check_snippet_friendly, check_concise_factual,
    # Module 6 – Information Gain
    check_generic_copy, check_thin_content, check_examples_proof, check_unique_insights,
    # Module 7 – GEO Opportunity
    compute_geo_opportunity,
)


@dataclass
class ModuleScore:
    module: str
    score: int
    icon: str
    checks: List[CheckResult] = field(default_factory=list)


@dataclass
class GeoReport:
    citation_readiness: ModuleScore
    entity_clarity: ModuleScore
    extractability: ModuleScore
    trust_signals: ModuleScore
    overview_readiness: ModuleScore
    information_gain: ModuleScore
    geo_opportunity: object          # GeoOpportunityResult
    geo_score: int                   # Average of modules 1–6
    overall_ai_score: int            # Blend of geo_score + legacy AI checks


def _mod_score(checks: List[CheckResult]) -> int:
    total = sum(c.score for c in checks)
    mx = sum(c.max_score for c in checks)
    return round(total / mx * 100) if mx else 0


def score(page, legacy_ai_score: int = 0) -> GeoReport:
    """Run all 6 primary GEO modules + opportunity module."""

    # ── Module 1: AI Citation Readiness ────────────────────────────────────
    citation_checks = [c for c in [
        check_service_definitions(page),
        check_faq_for_citation(page),
        check_summary_for_citation(page),
        check_structured_formatting(page),
        check_extractable_answers(page),
    ] if c]
    citation = ModuleScore("AI Citation Readiness", _mod_score(citation_checks), "🤖", citation_checks)

    # ── Module 2: Brand / Entity Clarity ───────────────────────────────────
    entity_checks = [c for c in [
        check_business_clarity(page),
        check_services_listed(page),
        check_industry_category(page),
        check_brand_consistency(page),
    ] if c]
    entity = ModuleScore("Brand / Entity Clarity", _mod_score(entity_checks), "🏢", entity_checks)

    # ── Module 3: AI Extractability ────────────────────────────────────────
    extract_checks = [c for c in [
        check_short_answer_paragraphs(page),
        check_definition_content(page),
        check_structured_lists(page),
        check_scannable_formatting(page),
        check_comparison_content(page),
    ] if c]
    extractability = ModuleScore("AI Extractability", _mod_score(extract_checks), "⚡", extract_checks)

    # ── Module 4: AI Trust Signals ─────────────────────────────────────────
    trust_checks = [c for c in [
        check_testimonials(page),
        check_case_studies(page),
        check_about_team(page),
        check_trust_badges(page),
        check_contact_transparency(page),
    ] if c]
    trust = ModuleScore("AI Trust Signals", _mod_score(trust_checks), "🛡️", trust_checks)

    # ── Module 5: AI Overview Readiness ────────────────────────────────────
    overview_checks = [c for c in [
        check_qa_formatting(page),
        check_informational_structure(page),
        check_snippet_friendly(page),
        check_concise_factual(page),
    ] if c]
    overview = ModuleScore("AI Overview Readiness", _mod_score(overview_checks), "📋", overview_checks)

    # ── Module 6: Information Gain / Originality ───────────────────────────
    originality_checks = [c for c in [
        check_generic_copy(page),
        check_thin_content(page),
        check_examples_proof(page),
        check_unique_insights(page),
    ] if c]
    originality = ModuleScore("Information Gain / Originality", _mod_score(originality_checks), "💡", originality_checks)

    # ── Module 7: GEO Opportunity ──────────────────────────────────────────
    geo_opp = compute_geo_opportunity(
        citation_score=citation.score,
        entity_score=entity.score,
        extractability_score=extractability.score,
        trust_score=trust.score,
        overview_score=overview.score,
        originality_score=originality.score,
        seo_score=0,
    )

    # GEO Score = average of 6 primary modules
    geo_score = round((citation.score + entity.score + extractability.score +
                       trust.score + overview.score + originality.score) / 6)

    # Overall AI Score blends legacy AI checks + GEO
    overall_ai = round((legacy_ai_score * 0.35 + geo_score * 0.65))

    return GeoReport(
        citation_readiness=citation,
        entity_clarity=entity,
        extractability=extractability,
        trust_signals=trust,
        overview_readiness=overview,
        information_gain=originality,
        geo_opportunity=geo_opp,
        geo_score=geo_score,
        overall_ai_score=overall_ai,
    )