
from dataclasses import dataclass, field
from typing import List
from .checks import *

@dataclass
class ModuleResult:
    module: str; score: int
    checks: List[CheckResult] = field(default_factory=list)

def score(page, keyword: str = "") -> ModuleResult:
    kw = keyword.strip()
    raw = [
        check_faq(page, kw),
        check_summary(page, kw),
        check_readability(page),
        check_answer_friendly(page, kw),
        check_featured_snippet_format(page, kw),
        check_topic_depth(page),
        check_writing_style(page),
        check_long_tail_keywords(page, kw),
        check_internal_links(page),
        check_external_links(page),
        check_voice_search(page, kw),
        check_tone(page),
        check_search_intent(page, kw),
    ]
    checks = [c for c in raw if c is not None]
    total = sum(c.score for c in checks)
    mx = sum(c.max_score for c in checks)
    return ModuleResult(module="AI Score", score=round(total/mx*100) if mx else 0, checks=checks)