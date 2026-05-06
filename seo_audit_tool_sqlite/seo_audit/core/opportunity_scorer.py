"""
opportunity_scorer.py
Scores the Opportunity module (max 100 pts).
This score reflects how much room for improvement exists — higher gaps = lower score.
It aggregates failed/warned checks from other modules into a clear opportunity signal.
"""

from .seo_scorer import CheckResult, ModuleResult


def score(seo_result, content_result, ai_result) -> ModuleResult:
    checks = []
    total = 0

    all_checks = (
        seo_result.checks +
        content_result.checks +
        ai_result.checks
    )

    fails = [c for c in all_checks if c.status == "fail"]
    warns = [c for c in all_checks if c.status == "warn"]
    passes = [c for c in all_checks if c.status == "pass"]

    total_checks = len(all_checks)

    # ── Missing critical elements (40 pts) ───────────────────────────────────
    critical_items = [c for c in fails if c.max_score >= 14]
    if not critical_items:
        checks.append(CheckResult("Critical gaps", 40, 40, "pass",
            "No critical SEO or AI elements are missing.",
            "Strong foundation — focus on optimisation rather than fixing fundamentals."))
        total += 40
    elif len(critical_items) <= 2:
        pts = 20
        names = ", ".join(c.name for c in critical_items)
        checks.append(CheckResult("Critical gaps", pts, 40, "warn",
            f"{len(critical_items)} critical issue(s): {names}.",
            "Fixing these will have the highest impact on both search rankings and AI visibility."))
        total += pts
    else:
        pts = 5
        names = ", ".join(c.name for c in critical_items[:3])
        checks.append(CheckResult("Critical gaps", pts, 40, "fail",
            f"{len(critical_items)} critical gaps found: {names}{', and more' if len(critical_items)>3 else ''}.",
            "Multiple critical elements are missing. This site needs a full SEO and AI visibility overhaul."))
        total += pts

    # ── Improvement potential (30 pts) ───────────────────────────────────────
    warn_score_gap = sum(c.max_score - c.score for c in warns)
    max_warn_gap = sum(c.max_score for c in all_checks)  # theoretical max
    if max_warn_gap > 0:
        gap_ratio = warn_score_gap / max_warn_gap
    else:
        gap_ratio = 0

    if gap_ratio < 0.1:
        checks.append(CheckResult("Improvement potential", 30, 30, "pass",
            "Very few partial issues — site is well-optimised.",
            "Marginal improvements available; site is near best-practice."))
        total += 30
    elif gap_ratio < 0.25:
        checks.append(CheckResult("Improvement potential", 20, 30, "warn",
            f"{len(warns)} items scoring below maximum — moderate improvement room.",
            "A targeted optimisation sprint could meaningfully improve scores."))
        total += 20
    elif gap_ratio < 0.45:
        checks.append(CheckResult("Improvement potential", 10, 30, "warn",
            f"{len(warns)} items with significant gaps — substantial room to improve.",
            "Systematic optimisation across content and technical elements would drive strong ranking gains."))
        total += 10
    else:
        checks.append(CheckResult("Improvement potential", 3, 30, "fail",
            f"High improvement potential — many checks are underperforming.",
            "Comprehensive optimisation required across all four pillars."))
        total += 3

    # ── Quick win count (30 pts) ─────────────────────────────────────────────
    # Quick wins = failed checks with low max_score (easy fixes)
    quick_wins = [c for c in fails if c.max_score <= 16]
    if not quick_wins:
        checks.append(CheckResult("Quick wins available", 30, 30, "pass",
            "No easy-fix items missing — good baseline optimisation.",
            "Investment should focus on strategic content and AI optimisation."))
        total += 30
    elif len(quick_wins) <= 2:
        pts = 18
        names = ", ".join(c.name for c in quick_wins)
        checks.append(CheckResult("Quick wins available", pts, 30, "warn",
            f"{len(quick_wins)} quick win(s) identified: {names}.",
            "These can be fixed in under an hour and will immediately improve scores."))
        total += pts
    else:
        pts = 6
        names = ", ".join(c.name for c in quick_wins[:3])
        checks.append(CheckResult("Quick wins available", pts, 30, "fail",
            f"{len(quick_wins)} quick wins available: {names}, and more.",
            "Multiple low-effort fixes available — prioritise these for fastest ROI."))
        total += pts

    # Build top recommendations list (attached to module for UI display)
    top_recs = []
    # Prioritise: fails first by max_score desc, then warns
    sorted_issues = sorted(fails, key=lambda c: c.max_score, reverse=True) + \
                    sorted(warns, key=lambda c: (c.max_score - c.score), reverse=True)
    for c in sorted_issues[:5]:
        top_recs.append({
            "name": c.name,
            "finding": c.finding,
            "impact": c.impact,
            "status": c.status,
        })

    max_possible = sum(c.max_score for c in checks)
    normalised = round((total / max_possible) * 100) if max_possible else 0

    result = ModuleResult(module="Opportunity Score", score=normalised, checks=checks)
    result.top_recommendations = top_recs  # attach extra data for UI
    result.stats = {
        "passes": len(passes),
        "warnings": len(warns),
        "failures": len(fails),
        "total": total_checks,
    }
    return result
