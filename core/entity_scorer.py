"""
entity_scorer.py
Runs Section 3: Entity & Knowledge Graph Optimization.
Returns EntityReport with one ModuleScore.
"""
from dataclasses import dataclass, field
from typing import List
from .geo_checks import CheckResult
from .entity_checks import (
    check_brand_mention_density,
    check_same_as_links,
    check_nap_consistency,
    check_co_citation,
    check_knowledge_panel_eligibility,
)


@dataclass
class ModuleScore:
    module: str
    score: int
    icon: str
    checks: List[CheckResult] = field(default_factory=list)


@dataclass
class EntityReport:
    entity_kg: ModuleScore
    entity_score: int


def _mod_score(checks):
    total = sum(c.score for c in checks)
    mx = sum(c.max_score for c in checks)
    return round(total / mx * 100) if mx else 0


def score(page) -> EntityReport:
    checks = [c for c in [
        check_brand_mention_density(page),
        check_same_as_links(page),
        check_nap_consistency(page),
        check_co_citation(page),
        check_knowledge_panel_eligibility(page),
    ] if c]
    mod = ModuleScore("Entity & Knowledge Graph", _mod_score(checks), "🕸️", checks)
    return EntityReport(entity_kg=mod, entity_score=mod.score)
