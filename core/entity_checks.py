"""
entity_checks.py
Section 3: Entity & Knowledge Graph Optimization
"""
import re
from .geo_checks import CheckResult

INDUSTRY_ENTITIES = [
    "google", "microsoft", "salesforce", "hubspot", "shopify", "wordpress",
    "aws", "azure", "slack", "notion", "stripe", "zendesk", "atlassian",
    "gartner", "forrester", "deloitte", "mckinsey", "accenture",
]


def check_brand_mention_density(page, kw=None):
    """Brand name mention density — consistent entity presence throughout content."""
    domain_name = page.domain.split(".")[0].lower()
    full_lower = page.full_text.lower()
    mentions = full_lower.count(domain_name)
    density = (mentions / page.word_count * 1000) if page.word_count else 0  # per 1000 words
    # Also check in title/headings
    in_title = domain_name in page.title.lower()
    in_h1 = any(domain_name in h.lower() for h in page.h1_tags)
    prominent = in_title or in_h1
    if mentions >= 5 and prominent:
        return CheckResult("Brand name mention density", 3, 3, "pass",
            f"Brand '{domain_name}' mentioned {mentions} times ({density:.1f}/1000 words) — strong entity presence.",
            "Consistent brand mentions reinforce entity recognition across AI knowledge systems.",
            "No action needed.", effort="quick")
    if mentions >= 2:
        return CheckResult("Brand name mention density", 2, 3, "warn",
            f"Brand '{domain_name}' mentioned {mentions} times — more repetition strengthens entity signals.",
            "Weak brand repetition reduces AI entity confidence and Knowledge Panel eligibility.",
            f"Use '{domain_name}' naturally 5+ times per page. Include in H1, opening paragraph, and conclusion.",
            effort="quick")
    return CheckResult("Brand name mention density", 0, 3, "fail",
        f"Brand name '{domain_name}' mentioned only {mentions} time(s) in content.",
        "AI systems use brand mentions to build entity profiles — absence weakens AI brand presence.",
        f"Include brand name naturally in H1, first paragraph, headings, and throughout body content.",
        effort="quick")


def check_same_as_links(page, kw=None):
    """SameAs / external entity links — Wikipedia, LinkedIn, Crunchbase reinforce entity in LLM knowledge."""
    same_as = page.same_as_links
    entity_links = page.external_entity_links
    all_entity = list(set(list(entity_links.keys()) + (["sameAs"] if same_as else [])))
    found_platforms = list(entity_links.keys())
    if same_as and len(found_platforms) >= 2:
        return CheckResult("SameAs / external entity links", 3, 3, "pass",
            f"SameAs links in schema + external entity links found: {', '.join(found_platforms[:4])}.",
            "SameAs links and entity links reinforce brand entity in LLM knowledge graphs.",
            "No action needed. Add Wikipedia and Crunchbase links to Organization sameAs if missing.",
            effort="medium")
    if same_as or found_platforms:
        present = same_as[:2] if same_as else found_platforms[:2]
        return CheckResult("SameAs / external entity links", 2, 3, "warn",
            f"Some entity links found ({', '.join(found_platforms[:3])}) but sameAs schema links missing or sparse.",
            "LLMs train on entity link co-occurrence — more links = stronger brand entity signals.",
            "Add sameAs array to Organization schema with: Wikipedia URL, LinkedIn, Crunchbase, G2 profile.",
            effort="medium")
    return CheckResult("SameAs / external entity links", 0, 3, "fail",
        "No SameAs schema links or external entity profile links detected.",
        "Without entity links, AI systems cannot cross-reference your brand in knowledge graphs.",
        "Add sameAs to Organization schema: [Wikipedia URL, LinkedIn, Crunchbase]. Link to these from your about page.",
        effort="medium")


def check_nap_consistency(page, kw=None):
    """NAP consistency — Name, Address, Phone consistent across page and schema."""
    schema_nap = page.schema_nap
    text_phone = page.nap_phone
    schema_phone = schema_nap.get("phone", "")
    schema_name = schema_nap.get("name", "")
    domain_name = page.domain.split(".")[0].lower()
    has_schema_nap = bool(schema_name or schema_phone)
    has_text_phone = bool(text_phone)
    if has_schema_nap and has_text_phone:
        phone_match = (schema_phone.replace(" ", "").replace("-", "") in
                       text_phone.replace(" ", "").replace("-", "")) if schema_phone else True
        if phone_match:
            return CheckResult("NAP consistency (Name/Address/Phone)", 3, 3, "pass",
                f"NAP signals consistent: schema name '{schema_name}', phone in both schema and page text.",
                "Consistent NAP across page and schema improves Local SEO and AI entity accuracy.",
                "No action needed. Ensure consistency across all pages and Google Business Profile.",
                effort="medium")
        return CheckResult("NAP consistency (Name/Address/Phone)", 1, 3, "warn",
            f"NAP mismatch: phone in schema ('{schema_phone}') differs from visible text ('{text_phone[:20]}').",
            "NAP inconsistencies confuse AI systems and reduce local entity confidence.",
            "Ensure phone number is identical in Organization schema, page text, and Google Business Profile.",
            effort="medium")
    if has_schema_nap or has_text_phone:
        return CheckResult("NAP consistency (Name/Address/Phone)", 2, 3, "warn",
            f"Partial NAP: {'schema has contact info' if has_schema_nap else 'visible phone found'} but not both.",
            "Partial NAP reduces AI local entity confidence.",
            "Add full NAP (name, address, phone) to both Organization schema and visible page content.",
            effort="medium")
    return CheckResult("NAP consistency (Name/Address/Phone)", 0, 3, "fail",
        "No NAP signals detected in schema or page content.",
        "Without NAP data, AI cannot build accurate local entity profiles for your business.",
        "Add Organization schema with telephone and address. Display contact info visibly on the page.",
        effort="medium")


def check_co_citation(page, kw=None):
    """Co-citation detection — is the brand mentioned alongside established industry entities?"""
    full_lower = page.full_text.lower()
    domain_name = page.domain.split(".")[0].lower()
    found_entities = [e for e in INDUSTRY_ENTITIES if e in full_lower and e != domain_name]
    brand_present = domain_name in full_lower
    if found_entities and brand_present:
        return CheckResult("Co-citation detection", 3, 3, "pass",
            f"Brand co-cited alongside industry entities: {', '.join(found_entities[:5])}.",
            "Co-citation with established entities signals authority — LLMs train on these associations.",
            "No action needed. Continue mentioning industry context and comparisons.", effort="medium")
    if found_entities:
        return CheckResult("Co-citation detection", 2, 3, "warn",
            f"Industry entities mentioned ({', '.join(found_entities[:3])}) but brand name not prominent enough for co-citation.",
            "Weak co-citation reduces the likelihood of AI associating your brand with industry topics.",
            "Mention your brand name alongside industry context: 'Unlike [Entity], [Brand] does X...'",
            effort="medium")
    return CheckResult("Co-citation detection", 0, 3, "fail",
        "No co-citation with established industry entities detected.",
        "Without co-citation signals, AI systems have difficulty placing your brand in the right category.",
        "Add industry context: mention relevant platforms, compare with competitors, or cite industry reports.",
        effort="medium")


def check_knowledge_panel_eligibility(page, kw=None):
    """Knowledge Panel eligibility signals — combined schema + entity + Wikipedia signals."""
    signals = {
        "Organization schema": bool(page.organization_schema),
        "SameAs links in schema": bool(page.same_as_links),
        "Wikipedia link": "Wikipedia" in page.external_entity_links,
        "LinkedIn link": "LinkedIn" in page.external_entity_links or "linkedin" in page.social_links,
        "NAP in schema": bool(page.schema_nap.get("name")),
        "BreadcrumbList schema": page.has_breadcrumb_schema,
    }
    found = [k for k, v in signals.items() if v]
    missing = [k for k, v in signals.items() if not v]
    if len(found) >= 5:
        return CheckResult("Knowledge Panel eligibility", 3, 3, "pass",
            f"Strong Knowledge Panel signals: {', '.join(found)}.",
            "High Knowledge Panel eligibility signals increase AI entity recognition and citation probability.",
            "No action needed. Submit to Wikipedia and ensure Wikidata entry exists.", effort="complex")
    if len(found) >= 3:
        return CheckResult("Knowledge Panel eligibility", 2, 3, "warn",
            f"Moderate signals ({', '.join(found[:3])}). Missing: {', '.join(missing[:3])}.",
            "Improving Knowledge Panel signals directly improves AI citation probability.",
            f"Add: {', '.join(missing[:3])}. Aim for a Wikipedia article about your brand.",
            effort="complex")
    return CheckResult("Knowledge Panel eligibility", 0, 3, "fail",
        f"Low Knowledge Panel eligibility. Only {len(found)} of 6 signals present: {', '.join(found) or 'none'}.",
        "Without Knowledge Panel signals, AI systems treat your brand as an unknown entity.",
        "Priority: (1) Complete Organization schema, (2) Add sameAs links, (3) Create Wikipedia entry.",
        effort="complex")
