"""
ai_visibility_checks.py
AI Visibility — heuristic-based checks + live OpenAI testing (Phase 2).
Live AI tests query ChatGPT to verify brand recognition, keyword ranking, and sentiment.
"""
from typing import Optional, List
from .geo_checks import CheckResult
from .external_validator import ExternalValidationResult
from .ai_tester import AITestResult


def check_ai_bot_access_readiness(page) -> CheckResult:
    """Combined AI bot access readiness — llms.txt + robots.txt directives."""
    signals = {
        "llms.txt present": page.has_llms_txt,
        "robots.txt present": page.has_robots_txt,
        "XML sitemap": page.has_xml_sitemap,
    }
    # Check AI bot directives
    blocked = [b for b, v in page.robots_ai_directives.items() if v == "blocked"]
    allowed = [b for b, v in page.robots_ai_directives.items() if v == "allowed"]

    if blocked:
        signals["AI bots allowed"] = False
    elif allowed:
        signals["AI bots allowed"] = True
    else:
        signals["AI bots allowed"] = None  # no specific directives

    found = [k for k, v in signals.items() if v is True]
    issues = [k for k, v in signals.items() if v is False]

    if blocked:
        return CheckResult(
            "AI bot access readiness", 0, 4, "fail",
            f"AI bots are blocked: {', '.join(blocked)}. Other signals: {', '.join(found) or 'none'}.",
            "Blocking AI bots prevents your content from appearing in ChatGPT, Gemini, and Perplexity answers.",
            f"Remove Disallow rules for: {', '.join(blocked)}. Add explicit Allow: / for AI bots.",
            effort="quick")

    if len(found) >= 3:
        return CheckResult(
            "AI bot access readiness", 4, 4, "pass",
            f"Strong AI access signals: {', '.join(found)}. {', '.join(allowed[:3])} explicitly allowed.",
            "Your site is well-configured for AI crawler access — a prerequisite for AI visibility.",
            "No action needed. Monitor for new AI bots as they emerge.",
            effort="quick")
    if len(found) >= 1:
        return CheckResult(
            "AI bot access readiness", 2, 4, "warn",
            f"Partial AI access: {', '.join(found)}. Missing: {', '.join(issues)}.",
            "Incomplete AI access configuration may reduce visibility across AI platforms.",
            f"Add: {', '.join(issues)}. Prioritize llms.txt and AI bot directives in robots.txt.",
            effort="quick")
    return CheckResult(
        "AI bot access readiness", 0, 4, "fail",
        "No AI access signals found — AI systems may not be able to crawl your content.",
        "Without proper access configuration, AI systems cannot index or cite your content.",
        "Create llms.txt, add robots.txt with AI bot permissions, and ensure XML sitemap exists.",
        effort="quick")


def check_schema_ai_readiness(page) -> CheckResult:
    """Schema completeness for AI visibility."""
    key_schemas = {
        "Organization/LocalBusiness": bool(page.organization_schema),
        "BreadcrumbList": page.has_breadcrumb_schema,
        "Service schema": page.has_service_schema,
        "Author/Person": page.has_author_schema,
        "Content type (Article/HowTo/WebPage)": page.has_howto_article_schema,
        "FAQPage": page.has_faq_schema,
    }
    found = [k for k, v in key_schemas.items() if v]
    missing = [k for k, v in key_schemas.items() if not v]

    if len(found) >= 4:
        return CheckResult(
            "Schema AI readiness", 3, 3, "pass",
            f"Rich schema coverage for AI: {', '.join(found[:4])} ({len(found)}/6 key types).",
            "Comprehensive schema markup enables AI systems to build structured entity profiles.",
            "No action needed. Validate at Google Rich Results Test.",
            effort="medium")
    if len(found) >= 2:
        return CheckResult(
            "Schema AI readiness", 2, 3, "warn",
            f"Partial schema coverage: {', '.join(found[:3])}. Missing: {', '.join(missing[:3])}.",
            "Incomplete schema limits AI's ability to construct structured representations of your entity.",
            f"Add schema for: {', '.join(missing[:2])}.",
            effort="medium")
    return CheckResult(
        "Schema AI readiness", 0, 3, "fail",
        f"Minimal schema for AI visibility. Only found: {', '.join(found) or 'none'}. Missing: {', '.join(missing[:3])}.",
        "AI systems rely heavily on structured data — minimal schema severely limits AI visibility.",
        f"Priority: add Organization schema, then {', '.join(missing[:2])}.",
        effort="medium")


def check_content_citation_readiness(page) -> CheckResult:
    """Content readiness for AI citation based on extractability signals."""
    signals = {
        "FAQ section": page.has_faq_section,
        "Summary/TLDR": page.has_summary_section,
        "Definition content": page.definition_count >= 3,
        "Direct answers": page.direct_answer_count >= 3,
        "Structured lists": page.has_listicles,
        "Tables": page.has_table,
        "Question headings": sum(1 for h in page.all_headings if "?" in h) >= 2,
    }
    found = [k for k, v in signals.items() if v]
    missing = [k for k, v in signals.items() if not v]

    if len(found) >= 5:
        return CheckResult(
            "Content citation readiness", 3, 3, "pass",
            f"Strong citation-ready content: {', '.join(found[:5])} ({len(found)}/7 signals).",
            "Content is well-formatted for AI extraction and citation across all major AI platforms.",
            "No action needed. Continue producing answer-oriented, structured content.",
            effort="medium")
    if len(found) >= 3:
        return CheckResult(
            "Content citation readiness", 2, 3, "warn",
            f"Moderate citation readiness: {', '.join(found[:3])}. Missing: {', '.join(missing[:3])}.",
            "Adding more citation-friendly content formats would increase AI visibility.",
            f"Add: {', '.join(missing[:2])}.",
            effort="medium")
    return CheckResult(
        "Content citation readiness", 0, 3, "fail",
        f"Low citation readiness. Only {len(found)} signals. Missing: {', '.join(missing[:4])}.",
        "Content is not formatted for AI citation — unlikely to appear in AI-generated answers.",
        f"Add FAQ section, summary block, definition sentences, and question-format headings.",
        effort="medium")


def check_external_authority_for_ai(
    ext_validation: Optional[ExternalValidationResult] = None
) -> CheckResult:
    """External authority signals that boost AI visibility."""
    if ext_validation is None:
        return CheckResult(
            "External authority for AI visibility", 1, 3, "warn",
            "External profile validation not performed — cannot assess external authority for AI.",
            "External authority is a key factor in AI citation decisions.",
            "Re-run with full-site audit enabled to validate external profiles.",
            effort="quick")

    found = ext_validation.profiles_found
    wiki = ext_validation.wikipedia_detected
    wikidata = ext_validation.wikidata_detected

    if found >= 6 and (wiki or wikidata):
        return CheckResult(
            "External authority for AI visibility", 3, 3, "pass",
            f"Strong external authority: {found} platforms verified. Wikipedia: {'✅' if wiki else '❌'}. Wikidata: {'✅' if wikidata else '❌'}.",
            "Strong external authority signals significantly increase AI citation probability.",
            "No action needed. Maintain and update all external profiles.",
            effort="medium")
    if found >= 3:
        return CheckResult(
            "External authority for AI visibility", 2, 3, "warn",
            f"Moderate external authority: {found} platforms. Wikipedia: {'✅' if wiki else '❌'}. Wikidata: {'✅' if wikidata else '❌'}.",
            "Expanding external presence would improve AI citation probability.",
            f"Missing: {', '.join(ext_validation.profiles_missing[:3])}. Create profiles on these platforms.",
            effort="medium")
    return CheckResult(
        "External authority for AI visibility", 0, 3, "fail",
        f"Weak external authority: only {found} platforms confirmed. Wikipedia: {'✅' if wiki else '❌'}.",
        "Low external authority means AI systems have limited third-party signals to validate your brand.",
        "Priority: create LinkedIn, Trustpilot, and Clutch/G2 profiles. Work toward Wikipedia notability.",
        effort="medium")


def check_entity_recognition_readiness(page, ext_validation: Optional[ExternalValidationResult] = None) -> CheckResult:
    """Combined entity recognition readiness for AI platforms."""
    signals = {
        "Organization schema": bool(page.organization_schema),
        "SameAs links": bool(page.same_as_links),
        "Brand in title": page.domain.split(".")[0].lower() in page.title.lower() if page.title else False,
        "NAP data": bool(page.nap_phone or page.schema_nap.get("name")),
    }
    if ext_validation:
        signals["Wikipedia/Wikidata"] = ext_validation.wikipedia_detected or ext_validation.wikidata_detected
        signals["LinkedIn verified"] = any(
            p.platform == "LinkedIn" and p.exists for p in ext_validation.profiles
        )

    found = [k for k, v in signals.items() if v]
    missing = [k for k, v in signals.items() if not v]

    if len(found) >= 5:
        return CheckResult(
            "Entity recognition readiness", 3, 3, "pass",
            f"Strong entity recognition signals: {', '.join(found[:5])} ({len(found)}/{len(signals)}).",
            "AI systems can confidently identify and cite your brand entity.",
            "No action needed. Ensure entity data is consistent across all sources.",
            effort="medium")
    if len(found) >= 3:
        return CheckResult(
            "Entity recognition readiness", 2, 3, "warn",
            f"Moderate entity signals: {', '.join(found[:3])}. Missing: {', '.join(missing[:3])}.",
            "Additional entity signals would improve AI recognition and citation confidence.",
            f"Add: {', '.join(missing[:2])}.",
            effort="medium")
    return CheckResult(
        "Entity recognition readiness", 0, 3, "fail",
        f"Weak entity recognition: only {len(found)} signals. Missing: {', '.join(missing[:4])}.",
        "AI systems cannot confidently identify your brand — reducing citation probability.",
        f"Priority: add Organization schema with sameAs, ensure brand name in title, add NAP data.",
        effort="medium")


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE AI TEST CHECKS (Phase 2 — OpenAI-powered)
# ═══════════════════════════════════════════════════════════════════════════════

def check_ai_brand_recognition(ai_test: Optional[AITestResult] = None) -> Optional[CheckResult]:
    """Live test: Does ChatGPT recognise and know about the brand?"""
    if ai_test is None or not ai_test.tested:
        return None

    if ai_test.api_error:
        return CheckResult(
            "ChatGPT brand recognition (Live Test)", 0, 5, "warn",
            f"⚠️ AI test could not be completed: {ai_test.api_error}",
            "Live AI testing requires a valid OpenAI API key.",
            "Check your API key in Settings and try again.",
            effort="quick")

    q1 = ai_test.queries[0] if ai_test.queries else None
    if not q1 or q1.error:
        return CheckResult(
            "ChatGPT brand recognition (Live Test)", 0, 5, "warn",
            f"⚠️ Brand knowledge test failed: {q1.error if q1 else 'no query'}",
            "Could not test brand recognition with ChatGPT.",
            "Try again later or check your API key.",
            effort="quick")

    if q1.brand_mentioned and q1.sentiment == "positive" and q1.mention_count >= 3:
        return CheckResult(
            "ChatGPT brand recognition (Live Test)", 5, 5, "pass",
            f"✅ ChatGPT KNOWS your brand! Mentioned {q1.mention_count}x with {q1.sentiment} sentiment. "
            f"Response length: {len(q1.response)} chars — strong knowledge depth.",
            "ChatGPT has substantial knowledge about your brand — this is the gold standard for AI visibility.",
            "No action needed. Continue building brand signals to maintain AI knowledge freshness.",
            effort="complex")
    if q1.brand_mentioned and q1.mention_count >= 1:
        return CheckResult(
            "ChatGPT brand recognition (Live Test)", 3, 5, "warn",
            f"⚠️ ChatGPT has LIMITED knowledge of your brand. Mentioned {q1.mention_count}x, "
            f"sentiment: {q1.sentiment}. Response was {len(q1.response)} chars.",
            "ChatGPT recognizes your brand but lacks deep knowledge — AI may not cite you confidently.",
            "Strengthen brand signals: more press coverage, Wikipedia presence, structured data, authoritative backlinks.",
            effort="complex")
    return CheckResult(
        "ChatGPT brand recognition (Live Test)", 0, 5, "fail",
        "❌ ChatGPT does NOT recognise your brand. The AI had no knowledge of your company.",
        "Your brand is invisible to ChatGPT — it cannot mention or recommend you to users.",
        "Priority: build Wikipedia/Wikidata presence, get press coverage, create authoritative content, "
        "ensure structured data (Organization schema with sameAs links), and build third-party citations.",
        effort="complex")


def check_ai_keyword_ranking(ai_test: Optional[AITestResult] = None) -> Optional[CheckResult]:
    """Live test: Is the brand recommended when users search for target keyword?"""
    if ai_test is None or not ai_test.tested:
        return None

    if ai_test.api_error:
        return None  # Already reported in brand recognition check

    q2 = ai_test.queries[1] if len(ai_test.queries) > 1 else None
    if not q2 or q2.error:
        return None

    competitors_str = ""
    if q2.competitor_mentions:
        competitors_str = f" Competitors mentioned: {', '.join(q2.competitor_mentions[:5])}."

    if q2.brand_mentioned and q2.position == "first":
        return CheckResult(
            "ChatGPT keyword ranking (Live Test)", 5, 5, "pass",
            f"✅ Your brand is RANKED #1 by ChatGPT for your target keyword! "
            f"Position: {q2.position}. Mentions: {q2.mention_count}.{competitors_str}",
            "First position in AI recommendations is the highest visibility achievement.",
            "No action needed. Monitor regularly as AI rankings change.",
            effort="complex")
    if q2.brand_mentioned and q2.position == "top3":
        return CheckResult(
            "ChatGPT keyword ranking (Live Test)", 4, 5, "pass",
            f"✅ Your brand is in the TOP 3 ChatGPT recommendations! "
            f"Position: {q2.position}. Mentions: {q2.mention_count}.{competitors_str}",
            "Top 3 positioning in AI answers means strong keyword visibility.",
            "Strengthen brand signals and content relevance to move toward #1 position.",
            effort="complex")
    if q2.brand_mentioned:
        return CheckResult(
            "ChatGPT keyword ranking (Live Test)", 2, 5, "warn",
            f"⚠️ Brand is MENTIONED but not in the top 3 for your keyword. "
            f"Position: {q2.position}. Mentions: {q2.mention_count}.{competitors_str}",
            "Your brand is known but not strongly recommended for this keyword.",
            "Optimize content around target keyword, build more relevant case studies and testimonials, "
            "create comparison pages.",
            effort="complex")
    return CheckResult(
        "ChatGPT keyword ranking (Live Test)", 0, 5, "fail",
        f"❌ Brand NOT mentioned by ChatGPT for your target keyword."
        f"{competitors_str}",
        "ChatGPT does not recommend your brand for this keyword — competitors have stronger AI visibility.",
        "Analyze the competitors ChatGPT recommends. Strengthen your keyword-relevant content, "
        "build more authoritative backlinks, and create content that AI can cite.",
        effort="complex")


def check_ai_sentiment(ai_test: Optional[AITestResult] = None) -> Optional[CheckResult]:
    """Live test: What is the overall AI sentiment about the brand?"""
    if ai_test is None or not ai_test.tested:
        return None

    if ai_test.api_error or not ai_test.brand_recognized:
        return None  # No point checking sentiment if brand isn't recognized

    if ai_test.overall_sentiment == "positive":
        return CheckResult(
            "ChatGPT brand sentiment (Live Test)", 3, 3, "pass",
            f"✅ ChatGPT has POSITIVE sentiment about your brand. "
            f"Total mentions across tests: {ai_test.total_mentions}.",
            "Positive AI sentiment means ChatGPT is likely to recommend and cite your brand favorably.",
            "No action needed. Continue building positive brand signals.",
            effort="complex")
    if ai_test.overall_sentiment == "neutral":
        return CheckResult(
            "ChatGPT brand sentiment (Live Test)", 2, 3, "warn",
            f"⚠️ ChatGPT has NEUTRAL sentiment about your brand. "
            f"Total mentions: {ai_test.total_mentions}.",
            "Neutral sentiment means ChatGPT may mention you but won't actively recommend you.",
            "Build stronger differentiators: unique case studies, awards, thought leadership content.",
            effort="complex")
    if ai_test.overall_sentiment == "negative":
        return CheckResult(
            "ChatGPT brand sentiment (Live Test)", 0, 3, "fail",
            f"❌ ChatGPT has NEGATIVE sentiment about your brand. "
            f"Total mentions: {ai_test.total_mentions}.",
            "Negative AI sentiment means ChatGPT may warn users against your brand.",
            "Investigate and address: negative reviews, PR issues, comparison content. "
            "Build positive third-party citations to counteract.",
            effort="complex")
    return CheckResult(
        "ChatGPT brand sentiment (Live Test)", 1, 3, "warn",
        f"🔍 Could not determine ChatGPT's sentiment about your brand.",
        "Insufficient data to assess AI sentiment.",
        "Try running the test again with more specific keywords.",
        effort="quick")


def check_ai_competitor_landscape(ai_test: Optional[AITestResult] = None) -> Optional[CheckResult]:
    """Live test: Who does ChatGPT consider as competitors?"""
    if ai_test is None or not ai_test.tested:
        return None

    if ai_test.api_error:
        return None

    competitors = ai_test.competitors_found
    if not competitors:
        return None

    q3 = ai_test.queries[2] if len(ai_test.queries) > 2 else None
    if not q3 or q3.error:
        return None

    if q3.brand_mentioned and q3.sentiment == "positive":
        return CheckResult(
            "ChatGPT competitor comparison (Live Test)", 3, 3, "pass",
            f"✅ ChatGPT FAVORABLY compares your brand to competitors. "
            f"Competitors identified: {', '.join(competitors[:6])}.",
            "Positive comparison positioning means AI favors your brand over alternatives.",
            f"Monitor competitors: {', '.join(competitors[:3])}. Maintain competitive advantages.",
            effort="complex")
    if q3.brand_mentioned:
        return CheckResult(
            "ChatGPT competitor comparison (Live Test)", 2, 3, "warn",
            f"⚠️ ChatGPT mentions your brand in competitive context but not as the top choice. "
            f"Competitors: {', '.join(competitors[:6])}.",
            "Your brand is in the competitive conversation but not positioned as the leader.",
            f"Create comparison content vs {', '.join(competitors[:3])}. Highlight unique differentiators.",
            effort="complex")
    return CheckResult(
        "ChatGPT competitor comparison (Live Test)", 0, 3, "fail",
        f"❌ ChatGPT does not include your brand in competitive comparisons. "
        f"AI-recognized competitors: {', '.join(competitors[:6])}.",
        "Your brand is absent from AI competitive analysis — competitors have stronger visibility.",
        f"Study what makes {', '.join(competitors[:2])} visible to AI. Build similar authority signals.",
        effort="complex")
