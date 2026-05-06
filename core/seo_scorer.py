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
        # Keyword checks
        check_keyword_in_url(page, kw),
        check_keyword_in_title(page, kw),
        check_keyword_in_description(page, kw),
        check_keyword_in_alt(page, kw),
        check_keyword_in_filename(page, kw),
        check_keyword_in_headings(page, kw),
        check_keyword_frequency(page, kw),
        check_keyword_first100(page, kw),
        check_keyword_emphasized(page, kw),
        check_keyword_synonyms(page, kw),
        # On-page
        check_title_length(page),
        check_description_length(page),
        check_heading_structure(page),
        check_alt_tags_present(page),
        check_word_count(page),
        check_topic_coverage(page, kw),
        check_related_keywords(page, kw),
        # Technical
        check_seo_friendly_url(page),
        check_domain_length(page),
        check_ssl(page),
        check_robots_txt(page),
        check_favicon(page),
        check_canonical(page),
        check_html_sitemap(page),
        check_xml_sitemap(page),
        check_page_speed(page),
        check_http_requests(page),
        check_viewport(page),
        check_mobile_friendly(page),
        check_apple_icon(page),
        check_schema(page),
        check_indexability(page),
        check_og_tags(page),
    ]
    checks = [c for c in raw if c is not None]
    total = sum(c.score for c in checks)
    mx = sum(c.max_score for c in checks)
    return ModuleResult(module="SEO Score", score=round(total/mx*100) if mx else 0, checks=checks)

