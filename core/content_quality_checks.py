"""
content_quality_checks.py
Section 6: Content Quality & LLM Readability
Section 5 gaps: Author credibility, Source citations
Section 7: Off-Page & Citation Authority (heuristic)
"""
import re
from datetime import datetime, timezone
from .geo_checks import CheckResult


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: CONTENT QUALITY & LLM READABILITY
# ═══════════════════════════════════════════════════════════════════════════

def check_statistics_density(page, kw=None):
    """Statistics / data point density — AI engines prioritise citing specific numbers."""
    count = page.statistics_count
    density = (count / page.word_count * 1000) if page.word_count else 0
    if count >= 5:
        return CheckResult("Statistics / data point density", 3, 3, "pass",
            f"{count} data points detected ({density:.1f}/1000 words) — strong evidence-based content.",
            "AI engines prioritise citing specific data and statistics over generic claims.",
            "No action needed. Continue adding data-backed statements.", effort="medium")
    if count >= 2:
        return CheckResult("Statistics / data point density", 2, 3, "warn",
            f"Only {count} statistics or data points found — below recommended threshold.",
            "Low data density makes content appear generic — AI prefers citing evidence-backed sources.",
            "Add specific numbers: client counts, percentages, timeframes, dollar amounts, results.",
            effort="medium")
    return CheckResult("Statistics / data point density", 0, 3, "fail",
        f"No clear statistics or data points detected in content.",
        "Content without data is deprioritised by AI — AI engines prefer citing specific, verifiable facts.",
        "Add: 'We've helped 200+ clients…', '40% faster results…', '$2M revenue generated…'",
        effort="medium")


def check_quotable_sentences(page, kw=None):
    """Quotable sentence detection — standalone, citable factual sentences (X does Y)."""
    count = page.quotable_sentence_count
    if count >= 8:
        return CheckResult("Quotable sentence detection", 3, 3, "pass",
            f"{count} quotable, citable sentences detected — excellent AI citation material.",
            "Standalone factual sentences are the primary format AI uses for direct citations.",
            "No action needed.", effort="medium")
    if count >= 4:
        return CheckResult("Quotable sentence detection", 2, 3, "warn",
            f"Only {count} clearly quotable sentences — AI may have difficulty extracting standalone facts.",
            "Insufficient quotable content reduces citation probability in AI-generated answers.",
            "Write more standalone factual sentences: '[Service] is [clear description that stands alone].'",
            effort="medium")
    return CheckResult("Quotable sentence detection", 0, 3, "fail",
        f"Very few quotable sentences found ({count}). Most content is not independently citable.",
        "Content that cannot stand alone is rarely cited by AI in generated answers.",
        "Rewrite key sections as self-contained factual statements. Avoid pronoun-heavy, context-dependent sentences.",
        effort="medium")


def check_content_freshness(page, kw=None):
    """Content freshness / last updated date — AI engines favour recently updated content."""
    date_str = page.date_modified
    if not date_str:
        return CheckResult("Content freshness / last updated date", 0, 3, "fail",
            "No publish/update date detected in schema, meta tags, or visible <time> elements.",
            "AI engines favour recently updated content — undated content appears stale.",
            "Add dateModified to Article/WebPage schema. Add a visible 'Last updated: [date]' on the page.",
            effort="quick")
    try:
        date_str_clean = date_str[:10]
        pub_date = datetime.strptime(date_str_clean, "%Y-%m-%d")
        days_old = (datetime.now() - pub_date).days
        if days_old <= 90:
            return CheckResult("Content freshness / last updated date", 3, 3, "pass",
                f"Content updated recently: {date_str_clean} ({days_old} days ago) — fresh signal.",
                "Fresh content is prioritised by AI systems for accuracy and citation reliability.",
                "No action needed. Keep content updated quarterly.", effort="quick")
        if days_old <= 365:
            return CheckResult("Content freshness / last updated date", 2, 3, "warn",
                f"Content dated {date_str_clean} ({days_old} days ago) — could be refreshed.",
                "Content over 3 months old is flagged as potentially stale by AI systems.",
                "Update content with current statistics and examples. Update dateModified in schema.",
                effort="quick")
        return CheckResult("Content freshness / last updated date", 0, 3, "fail",
            f"Content appears stale: last updated {date_str_clean} ({days_old} days ago).",
            "Content over a year old is significantly deprioritised by AI citation systems.",
            "Refresh content with current data. Update dateModified schema field and add 'Updated [month year]' label.",
            effort="quick")
    except Exception:
        return CheckResult("Content freshness / last updated date", 1, 3, "warn",
            f"Date found ({date_str[:20]}) but could not be parsed as a standard date.",
            "Unparseable dates reduce AI confidence in content freshness signals.",
            "Use ISO 8601 format in schema: dateModified: '2024-05-15'. Validate at Rich Results Test.",
            effort="quick")


def check_reading_clarity(page, kw=None):
    """Reading level / clarity — mid-complexity prose is optimal for LLM readability."""
    score = page.readability_score
    if score == 0:
        return CheckResult("Reading level / clarity score", 1, 3, "warn",
            "Insufficient content to calculate reading clarity score.",
            "Readable content improves both human engagement and AI snippet extraction.",
            "Add more content. Target Flesch Reading Ease 50–70 (mid-complexity).", effort="medium")
    if 50 <= score <= 75:
        return CheckResult("Reading level / clarity score", 3, 3, "pass",
            f"Flesch Reading Ease: {score:.0f} — mid-complexity, ideal for LLM readability.",
            "Mid-complexity prose is optimal: clear enough to extract, substantive enough to cite.",
            "No action needed.", effort="medium")
    if score > 75:
        return CheckResult("Reading level / clarity score", 2, 3, "warn",
            f"Flesch Reading Ease: {score:.0f} — very easy/simple. May appear thin to AI.",
            "Overly simple content can signal lack of depth or expertise to AI systems.",
            "Add technical depth, specific examples, and nuanced explanations alongside plain language.",
            effort="medium")
    if score >= 30:
        return CheckResult("Reading level / clarity score", 2, 3, "warn",
            f"Flesch Reading Ease: {score:.0f} — complex. Harder for AI to extract clean snippets.",
            "Dense text reduces AI extraction accuracy and citation likelihood.",
            "Simplify sentences (under 20 words). Use active voice. Break up dense paragraphs.",
            effort="medium")
    return CheckResult("Reading level / clarity score", 0, 3, "fail",
        f"Flesch Reading Ease: {score:.0f} — very complex, academic-level text.",
        "Highly complex content is rarely selected for AI answer extraction.",
        "Rewrite using shorter sentences, plain language, active voice. Target score 50–70.",
        effort="medium")


def check_conversational_match(page, kw=None):
    """Conversational query match — does content answer natural language questions?"""
    q_headings = [h for h in page.all_headings if "?" in h]
    full_lower = page.full_text.lower()
    conversational_phrases = [
        "how to", "what is", "why does", "when should", "which is",
        "can you", "do you", "should i", "how does", "what are"
    ]
    conv_hits = sum(1 for p in conversational_phrases if p in full_lower)
    total_signals = len(q_headings) + conv_hits
    if total_signals >= 6 and len(q_headings) >= 2:
        return CheckResult("Conversational query match", 3, 3, "pass",
            f"{len(q_headings)} question headings + {conv_hits} conversational phrases — strong match.",
            "Conversational content mirrors how users phrase queries to ChatGPT and Perplexity.",
            "No action needed. Ensure each question heading has a direct 1-2 sentence answer.",
            effort="medium")
    if total_signals >= 3:
        return CheckResult("Conversational query match", 2, 3, "warn",
            f"Some conversational signals: {len(q_headings)} question headings, {conv_hits} phrases.",
            "Limited conversational match reduces visibility for natural language AI queries.",
            "Add question-format H2/H3 headings. Use 'How to', 'What is', 'Why does' formats.",
            effort="medium")
    return CheckResult("Conversational query match", 0, 3, "fail",
        f"Very few conversational query signals found ({total_signals} total).",
        "Content written for keywords rather than natural language is poorly matched for AI search.",
        "Restructure content around questions users ask ChatGPT/Perplexity. Add FAQ section.",
        effort="medium")


def check_semantic_coverage(page, kw=None):
    """Semantic keyword coverage — are semantically related entities present?"""
    full_lower = page.full_text.lower()
    if not kw:
        unique_words = set(w for w in full_lower.split() if len(w) > 4)
        richness = len(unique_words) / max(page.word_count, 1)
        if richness >= 0.45:
            return CheckResult("Semantic keyword coverage", 3, 3, "pass",
                f"Strong vocabulary richness ({richness:.2f} unique/total ratio) — good semantic depth.",
                "Semantic richness signals topical expertise to AI ranking systems.",
                "No action needed. Add keyword target for deeper analysis.", effort="medium")
        return CheckResult("Semantic keyword coverage", 2, 3, "warn",
            f"Moderate vocabulary richness ({richness:.2f}). Provide target keyword for deeper analysis.",
            "Limited semantic variety can reduce topical authority signals.",
            "Add related terms, synonyms, and subtopics. Provide target keyword for detailed check.",
            effort="medium")
    kw_words = [w for w in kw.lower().split() if len(w) > 3]
    related_found = [w for w in kw_words if full_lower.count(w) > 1]
    if len(related_found) >= len(kw_words) * 0.8:
        return CheckResult("Semantic keyword coverage", 3, 3, "pass",
            f"Good semantic coverage for '{kw}': related terms {', '.join(related_found)} found throughout.",
            "Semantic keyword coverage signals topical depth and authority to AI search systems.",
            "No action needed. Add LSI keywords and related entities for even stronger signals.",
            effort="medium")
    return CheckResult("Semantic keyword coverage", 1, 3, "warn",
        f"Limited semantic coverage for '{kw}'. Only {len(related_found)}/{len(kw_words)} terms distributed.",
        "AI search engines evaluate semantic breadth — exact keyword alone is insufficient.",
        f"Include related terms, subtopics, and entities associated with '{kw}' throughout content.",
        effort="medium")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5 GAPS: Author Credibility + Source Citations
# ═══════════════════════════════════════════════════════════════════════════

def check_author_credibility(page, kw=None):
    """Author bio with credentials / expertise signals."""
    full_lower = page.full_text.lower()
    cred_signals = [
        "years of experience", "certified", "expert", "specialist", "founder",
        "ceo", "director", "phd", "mba", "degree", "qualified", "accredited",
        "author of", "published", "speaker", "consultant", "advisor"
    ]
    found = [s for s in cred_signals if s in full_lower]
    has_author_schema = page.has_author_schema
    if (len(found) >= 3 or has_author_schema) and found:
        return CheckResult("Author credibility signals", 3, 3, "pass",
            f"Author credibility signals detected: {', '.join(found[:4])}{' + Author schema' if has_author_schema else ''}.",
            "Author credibility signals are key E-E-A-T indicators — AI prefers citing credentialed sources.",
            "No action needed. Add LinkedIn author link and Person schema for maximum signal.", effort="quick")
    if found or has_author_schema:
        return CheckResult("Author credibility signals", 2, 3, "warn",
            f"Some credibility signals found ({', '.join(found[:2]) or 'Author schema only'}) — more depth needed.",
            "Weak author credibility reduces E-E-A-T score and AI citation confidence.",
            "Add author bio section with: years of experience, qualifications, role, and expertise areas.",
            effort="quick")
    return CheckResult("Author credibility signals", 0, 3, "fail",
        "No author credibility signals or bio found on this page.",
        "Anonymous content without credentials is assigned lower trust by AI systems.",
        "Add author bio with credentials, experience, and role. Link to LinkedIn. Add Person schema.",
        effort="quick")


def check_source_citations(page, kw=None):
    """Source citations — external references and data sources linked for claims."""
    full_lower = page.full_text.lower()
    citation_phrases = ["according to", "study shows", "research by", "reported by",
                        "source:", "data from", "based on research", "survey by", "as cited"]
    phrase_hits = sum(1 for p in citation_phrases if p in full_lower)
    trusted = page.trusted_external_links
    has_refs_heading = any("reference" in h.lower() or "source" in h.lower() or "citation" in h.lower()
                           for h in page.all_headings)
    total_signals = phrase_hits + trusted + (2 if has_refs_heading else 0)
    if total_signals >= 5:
        return CheckResult("Source citations", 3, 3, "pass",
            f"Strong citation signals: {phrase_hits} citation phrases, {trusted} trusted links, references section: {has_refs_heading}.",
            "Source citations significantly increase AI citation confidence and E-E-A-T scores.",
            "No action needed. Ensure all citations link to primary sources.", effort="medium")
    if total_signals >= 2:
        return CheckResult("Source citations", 2, 3, "warn",
            f"Partial citations: {phrase_hits} phrases, {trusted} trusted external links.",
            "Limited source citations reduce content credibility in AI systems.",
            "Add 'According to [Source]...' citations. Link to research, industry reports, or authoritative data.",
            effort="medium")
    return CheckResult("Source citations", 0, 3, "fail",
        "No source citations, references, or trusted external links found.",
        "Uncited claims are deprioritised by AI — AI systems prefer citing sources that cite sources.",
        "Add external citations to support key claims. Link to industry reports, studies, or news articles.",
        effort="medium")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: OFF-PAGE & CITATION AUTHORITY (heuristic)
# ═══════════════════════════════════════════════════════════════════════════

def check_social_profile_links(page, kw=None):
    """Social profile completeness — LinkedIn, Twitter/X, YouTube, industry directories."""
    social = page.social_links
    PRIORITY = ["linkedin", "twitter", "x", "youtube"]
    found = list(social.keys())
    priority_found = [p for p in PRIORITY if p in social]
    if len(found) >= 3 and priority_found:
        return CheckResult("Social profile completeness", 3, 3, "pass",
            f"Social profiles linked: {', '.join(found[:5])}.",
            "Social profiles strengthen AI entity profiles — LLMs train on social signals.",
            "No action needed. Ensure profiles are complete and active.", effort="quick")
    if found:
        return CheckResult("Social profile completeness", 2, 3, "warn",
            f"Some social links found ({', '.join(found[:3])}) — LinkedIn is most critical if missing.",
            "Incomplete social profile links weaken entity signals in AI knowledge graphs.",
            "Add links to: LinkedIn (most important for B2B), Twitter/X, YouTube. Link from footer/about page.",
            effort="quick")
    return CheckResult("Social profile completeness", 0, 3, "fail",
        "No social profile links detected on this page.",
        "Without social links, AI cannot cross-reference your entity across platforms.",
        "Add footer links to LinkedIn, Twitter/X, YouTube. Include in Organization sameAs schema.",
        effort="quick")


def check_review_platform_links(page, kw=None):
    """Review platform presence — G2, Clutch, Trustpilot, Google Business Reviews."""
    reviews = page.review_platform_links
    full_lower = page.full_text.lower()
    review_mentions = sum(1 for p in ["g2", "clutch", "trustpilot", "capterra", "google reviews"]
                          if p in full_lower)
    if reviews and len(reviews) >= 2:
        return CheckResult("Review platform presence", 3, 3, "pass",
            f"Review platform links detected: {', '.join(list(reviews.keys())[:4])}.",
            "LLMs heavily weight third-party review signals when assessing business credibility.",
            "No action needed. Actively collect reviews on these platforms.", effort="quick")
    if reviews or review_mentions >= 1:
        found_str = ', '.join(list(reviews.keys())[:2]) or "mentioned in text"
        return CheckResult("Review platform presence", 2, 3, "warn",
            f"Some review signals found ({found_str}) — more platforms recommended.",
            "Single-platform review presence is weaker than multi-platform citation coverage.",
            "Add links to G2, Clutch, and Trustpilot profiles. Display review widget on site.",
            effort="quick")
    return CheckResult("Review platform presence", 0, 3, "fail",
        "No review platform links or mentions detected.",
        "Without third-party reviews, AI systems have limited signals to assess your business credibility.",
        "Create profiles on G2, Clutch, Trustpilot. Link to them from your website. Collect reviews actively.",
        effort="quick")


def check_press_mentions(page, kw=None):
    """Press / media mentions — PR coverage is a strong LLM citation trust signal."""
    press_links = page.press_mention_links
    full_lower = page.full_text.lower()
    press_phrases = ["featured in", "as seen in", "press", "media coverage", "in the news",
                     "mentioned in", "covered by", "appeared in"]
    phrase_hits = sum(1 for p in press_phrases if p in full_lower)
    if press_links and len(press_links) >= 2:
        return CheckResult("Press / media mentions", 3, 3, "pass",
            f"Press mention links detected ({len(press_links)} outlets linked) — strong authority signal.",
            "PR coverage on news sites is a strong LLM citation trust signal — flag for AI brand presence.",
            "No action needed. Continue pursuing press coverage.", effort="complex")
    if press_links or phrase_hits >= 1:
        return CheckResult("Press / media mentions", 2, 3, "warn",
            f"Some press signals ({len(press_links)} links, {phrase_hits} phrases) — more coverage needed.",
            "Limited press coverage reduces brand authority signals in AI knowledge graphs.",
            "Add 'As Seen In' section with press logos. Pursue PR outreach to industry publications.",
            effort="complex")
    return CheckResult("Press / media mentions", 0, 3, "fail",
        "No press mention links or media coverage signals detected.",
        "Absence of press signals limits brand authority recognition in AI systems.",
        "Add a press/media section. Link to any existing coverage. Pursue PR outreach for industry publications.",
        effort="complex")
