"""checks.py — All 40+ individual check functions, each returns a CheckResult."""
import re
from dataclasses import dataclass

@dataclass
class CheckResult:
    name: str
    score: int
    max_score: int
    status: str       # pass | warn | fail
    found: str        # "What we found" — matches auditsky style
    impact: str       # Why it matters
    how_to_fix: str   # Actionable fix
    category: str = "SEO"
    details: list = None

def _kw_in(text: str, kw: str) -> bool:
    return bool(kw and text and kw.lower() in text.lower())

def _kw_count(text: str, kw: str) -> int:
    return text.lower().count(kw.lower()) if kw and text else 0

# ─────────────────────────── KEYWORD CHECKS ────────────────────────────────

def check_keyword_in_url(page, kw):
    if not kw:
        return None
    found = _kw_in(page.url_path, kw) or _kw_in(page.domain, kw)
    kw_slug = kw.lower().replace(" ", "-")
    if found:
        return CheckResult("Keyword in URL", 3, 3, "pass",
            f"Target keyword '{kw}' is present in the URL.",
            "Keyword in URL reinforces topical relevance and improves CTR in SERPs.",
            "No action needed.")
    return CheckResult("Keyword in URL", 0, 3, "fail",
        f"Target keyword '{kw}' is not in the URL.",
        "Missing keyword in URL is a missed relevance signal, especially for competitive queries.",
        f"Include '{kw}' in the URL slug where possible. E.g. /{kw_slug}/")

def check_keyword_in_title(page, kw):
    if not kw: return None
    if not page.title:
        return CheckResult("Keyword in title tag", 0, 4, "fail",
            "No title tag found — keyword check not possible.",
            "A missing title tag is a critical SEO issue.",
            f"Add <title>{kw.title()} – Your Brand</title> in <head>.")
    tl = page.title.lower()
    kl = kw.lower()
    details = [f"Evaluated title: <code>{page.title}</code>"]
    if tl.startswith(kl):
        return CheckResult("Keyword in title tag", 4, 4, "pass",
            f"Title tag starts with target keyword: \"{page.title[:70]}\"",
            "Front-loading keyword in title maximises relevance signals and CTR.",
            "No action needed.", details=details)
    elif kl in tl:
        pos = tl.find(kl)
        return CheckResult("Keyword in title tag", 3, 4, "warn",
            f"The title tag '{page.title[:70]}' does not start with the exact target keyword.",
            "Keywords at the start of title tags carry more weight than those in the middle or end.",
            f"Rewrite title to lead with '{kw}'. E.g. '{kw.title()} – {page.domain}'", details=details)
    return CheckResult("Keyword in title tag", 0, 4, "fail",
        f"The title tag '{page.title[:70]}' does not contain target keyword '{kw}'.",
        "Missing keyword in title is one of the highest-impact SEO gaps.",
        f"Include '{kw}' near the start of your title. Keep total length 50–60 chars.", details=details)

def check_keyword_in_description(page, kw):
    if not kw: return None
    m = page.meta_description
    if not m:
        return CheckResult("Keyword in description tag", 0, 3, "fail",
            "No meta description found.",
            "Zero control over SERP snippet — search engines generate their own.",
            f"Add <meta name='description' content='...'> containing '{kw}'. 120–160 chars.")
    details = [f"Evaluated meta description: <code>{m}</code>"]
    if _kw_in(m, kw):
        return CheckResult("Keyword in description tag", 3, 3, "pass",
            f"Description tag contains target keyword '{kw}'.",
            "Keyword in description leads to bold highlighting in SERPs, improving CTR.",
            "No action needed.", details=details)
    # Check synonyms / partial match
    kw_words = kw.lower().split()
    partial = sum(1 for w in kw_words if w in m.lower()) / len(kw_words)
    if partial >= 0.5:
        return CheckResult("Keyword in description tag", 2, 3, "warn",
            f"Description tag contains partial keyword match but not full phrase '{kw}'.",
            "Partial keyword match in description misses bold-highlighting opportunity.",
            f"Include the exact phrase '{kw}' naturally in your meta description.", details=details)
    return CheckResult("Keyword in description tag", 0, 3, "fail",
        f"Description tag '{m[:80]}...' does not contain '{kw}'.",
        "Missing keyword in description reduces CTR from search results.",
        f"Rewrite meta description to include '{kw}' naturally within 120–160 chars.", details=details)

def check_keyword_in_alt(page, kw):
    if not kw: return None
    if not page.images:
        return CheckResult("Keyword usage in alt tag", 2, 3, "pass",
            "No images found on this page.", "N/A", "No action needed.")
    matches = [img for img in page.images if _kw_in(img.get("alt",""), kw)]
    missing = [img for img in page.images if not _kw_in(img.get("alt",""), kw)]
    details = [f"Missing keyword in alt for: <strong>{img.get('src', 'Unknown')}</strong> <br><small><code>{str(img)[:100]}...</code></small>" for img in missing]
    if matches:
        return CheckResult("Keyword usage in alt tag", 3, 3, "pass",
            f"Target keyword '{kw}' found in {len(matches)} image alt tag(s).",
            "Keyword alt tags reinforce relevance and improve image search ranking.",
            "No action needed.", details=details if len(matches) < len(page.images) else None)
    return CheckResult("Keyword usage in alt tag", 0, 3, "fail",
        f"The target keyword '{kw}' was not explicitly found in any alt tags.",
        "Missing keyword in alt tags is a missed on-page relevance signal.",
        f"Add alt='{kw}' (or a natural variation) to your most prominent images.", details=details)

def check_keyword_in_filename(page, kw):
    if not kw: return None
    if not page.image_filenames:
        return CheckResult("Keyword usage in image filename", 2, 2, "pass",
            "No images found.", "N/A", "No action needed.")
    kw_slug = kw.lower().replace(" ", "-")
    matches = [f for f in page.image_filenames if _kw_in(f, kw) or _kw_in(f, kw_slug)]
    missing = [f for f in page.image_filenames if f not in matches]
    details = [f"Filename missing keyword: <code>{f}</code>" for f in missing]
    if matches:
        return CheckResult("Keyword usage in image filename", 2, 2, "pass",
            f"Target keyword found in image filename(s): {', '.join(matches[:3])}",
            "Keyword filenames provide extra context to image search algorithms.",
            "No action needed.", details=details if missing else None)
    return CheckResult("Keyword usage in image filename", 0, 2, "fail",
        f"The target keyword '{kw}' was not explicitly found in any image filenames.",
        "Image filenames are an easily-overlooked relevance signal for image SEO.",
        f"Rename images to include '{kw_slug}' before uploading. E.g. '{kw_slug}-example.jpg'", details=details)

def check_keyword_in_headings(page, kw):
    if not kw: return None
    kw_h1 = any(_kw_in(h, kw) for h in page.h1_tags)
    kw_h2 = any(_kw_in(h, kw) for h in page.h2_tags)
    kw_h3 = any(_kw_in(h, kw) for h in page.h3_tags)
    details = []
    if not kw_h1 and page.h1_tags:
        details.append("<strong>H1 tag missing keyword:</strong>")
        details.extend([f" - <code>{h}</code>" for h in page.h1_tags])
    if not kw_h2 and page.h2_tags:
        details.append("<strong>No H2 tags contain the keyword.</strong>")
    if not kw_h3 and page.h3_tags:
        details.append("<strong>No H3 tags contain the keyword.</strong>")

    if kw_h1 and (kw_h2 or kw_h3):
        return CheckResult("Keyword in heading tag", 4, 4, "pass",
            f"Target keyword '{kw}' found in H1 and H2/H3 headings.",
            "Strong keyword signals in heading hierarchy reinforce topical relevance.",
            "No action needed.", details=details if details else None)
    if kw_h1 or kw_h2 or kw_h3:
        level = "H1" if kw_h1 else ("H2" if kw_h2 else "H3")
        return CheckResult("Keyword in heading tag", 2, 4, "warn",
            f"Target keyword '{kw}' found only in {level} — not across multiple heading levels.",
            "Using keyword in multiple heading levels strengthens topical depth signals.",
            f"Add '{kw}' naturally to at least one H2 or H3 subheading.", details=details)
    return CheckResult("Keyword in heading tag", 0, 4, "fail",
        f"The exact target keyword '{kw}' was not explicitly found in H1, H2, or H3 tags.",
        "No keyword signals in headings significantly weakens on-page relevance.",
        f"Include '{kw}' in your H1 and at least one H2 heading.", details=details)

def check_keyword_frequency(page, kw):
    if not kw: return None
    freq = _kw_count(page.full_text, kw)
    density = (freq / page.word_count * 100) if page.word_count else 0
    if freq == 0:
        return CheckResult("Keyword frequency in content", 0, 3, "fail",
            f"The exact keyword '{kw}' is not explicitly present in the visible page content.",
            "Zero occurrences means the page sends no direct relevance signal for this query.",
            f"Use '{kw}' naturally in the introduction, body, and conclusion. Target 1–2% density.")
    if density < 0.5:
        return CheckResult("Keyword frequency in content", 1, 3, "warn",
            f"Keyword '{kw}' appears {freq} time(s) ({density:.1f}% density) — too sparse.",
            "Very low keyword density reduces relevance signal.",
            f"Increase usage to achieve 0.5–2% density. Also use semantic variants.")
    if density > 3.5:
        return CheckResult("Keyword frequency in content", 1, 3, "warn",
            f"Keyword '{kw}' appears {freq} times ({density:.1f}% density) — possible over-optimisation.",
            "Keyword stuffing above 3% can trigger spam filters.",
            f"Replace some instances with synonyms and related phrases.")
    return CheckResult("Keyword frequency in content", 3, 3, "pass",
        f"Keyword '{kw}' appears {freq} times ({density:.1f}% density) — well balanced.",
        "Natural keyword density signals relevance without over-optimisation.",
        "No action needed.")

def check_keyword_first100(page, kw):
    if not kw: return None
    if _kw_in(page.first_100_words, kw):
        return CheckResult("Keyword in first 100 words", 3, 3, "pass",
            f"Target keyword '{kw}' is present within the first 100 words.",
            "Early keyword placement confirms page topic to crawlers and reduces bounce rate.",
            "No action needed.")
    return CheckResult("Keyword in first 100 words", 0, 3, "fail",
        f"The exact keyword '{kw}' is not found within the first 100 words of visible content.",
        "Search engines weight early content higher — missing keyword here is a significant gap.",
        f"Rewrite your opening paragraph to naturally include '{kw}' within the first 50 words.")

def check_keyword_emphasized(page, kw):
    if not kw: return None
    if _kw_in(page.bold_italic_text, kw):
        return CheckResult("Keyword emphasized (bold/italic)", 2, 2, "pass",
            f"Target keyword '{kw}' is highlighted in bold or italic text.",
            "Formatted keywords draw reader attention and provide mild relevance signals.",
            "No action needed.")
    return CheckResult("Keyword emphasized (bold/italic)", 0, 2, "warn",
        f"The target keyword '{kw}' is not highlighted (e.g., bolded or italicized) on the page.",
        "Using bold/italic on key terms improves scannability and sends mild relevance signals.",
        f"Wrap '{kw}' in <strong>...</strong> at least once in your main content.")

def check_keyword_synonyms(page, kw):
    if not kw: return None
    words = kw.lower().split()
    full_lower = page.full_text.lower()
    synonyms_found = [w for w in words if full_lower.count(w) > 2]
    details = [f"Found term: <strong>{s}</strong> ({full_lower.count(s)}x)" for s in synonyms_found]
    if len(synonyms_found) >= 1 and page.word_count > 100:
        return CheckResult("Keyword synonyms used", 3, 3, "pass",
            f"Synonyms and related terms of '{kw}' are used throughout the content.",
            "Semantic variants signal topical depth to AI-powered search algorithms.",
            "No action needed. Consider adding more LSI keywords for even better coverage.", details=details)
    return CheckResult("Keyword synonyms used", 1, 3, "warn",
        f"Limited use of synonyms and related terms for '{kw}' detected.",
        "AI search engines reward semantic richness — exact keyword alone is not enough.",
        f"Use synonyms, related phrases, and LSI keywords alongside '{kw}' throughout content.", details=details)

# ─────────────────────────── CONTENT CHECKS ────────────────────────────────

def check_word_count(page, kw=None):
    wc = page.word_count
    if wc < 200:
        return CheckResult("Word count", 0, 4, "fail",
            f"The visible content word count is approximately {wc} words — very thin content.",
            "Thin pages rarely rank for competitive queries or appear in AI answer boxes.",
            "Expand content to at least 600–800 words. Add context, examples, FAQs, and step-by-step guides.")
    if wc < 500:
        return CheckResult("Word count", 2, 4, "warn",
            f"The visible content word count is approximately {wc} words — below recommended minimum.",
            "Under 500 words is considered thin for most topics.",
            "Aim for 800–1500 words. Add a FAQ section, how-to guide, or supporting examples.")
    if wc < 1000:
        return CheckResult("Word count", 3, 4, "warn",
            f"The visible content word count is approximately {wc} words, which is generally adequate.",
            "Adequate but may be thin for competitive keywords.",
            "Consider expanding to 1200+ words with deeper coverage and supporting content.")
    return CheckResult("Word count", 4, 4, "pass",
        f"The visible content word count is approximately {wc} words — comprehensive.",
        "Strong content length signals depth and authority to search engines.",
        "No action needed.")

def check_topic_coverage(page, kw):
    if not kw: return None
    kw_words = [w for w in kw.lower().split() if len(w) > 3]
    full_lower = page.full_text.lower()
    heading_lower = " ".join(page.all_headings).lower()
    found = [w for w in kw_words if w in full_lower]
    heading_match = any(w in heading_lower for w in kw_words)
    coverage = len(found) / len(kw_words) if kw_words else 0
    if coverage >= 0.8 and heading_match:
        return CheckResult("Keyword + topic matching", 3, 3, "pass",
            f"Target keyword topic '{kw}' is well covered across content and headings.",
            "Strong topic-keyword alignment signals content relevance to search engines.",
            "No action needed.")
    if coverage >= 0.5:
        return CheckResult("Keyword + topic matching", 2, 3, "warn",
            f"While related terms are present, the exact phrase '{kw}' is not explicitly used throughout.",
            "Partial topic coverage reduces keyword-to-intent alignment.",
            f"Ensure '{kw}' and its component words appear in headings, body, and meta tags.")
    return CheckResult("Keyword + topic matching", 0, 3, "fail",
        f"Topic coverage for '{kw}' is weak — key terms are largely absent from content.",
        "Poor topic-keyword match leads to low relevance scores and poor ranking.",
        f"Restructure content to focus on '{kw}'. Add dedicated sections, examples, and definitions.")

def check_related_keywords(page, kw):
    if not kw: return None
    full_lower = page.full_text.lower()
    # Detect LSI/related terms in page
    kw_words = kw.lower().split()
    related = []
    for w in kw_words:
        if len(w) > 3:
            count = full_lower.count(w)
            if count > 1:
                related.append(f"'{w}' ({count}x)")
    if len(related) >= 2:
        return CheckResult("Related keyword content detection", 3, 3, "pass",
            f"Related keyword terms detected: {', '.join(related[:6])}",
            "Semantic keyword coverage signals topical depth to AI search engines.",
            "No action needed. Consider adding more semantically related terms.")
    return CheckResult("Related keyword content detection", 1, 3, "warn",
        f"Limited related keyword coverage for '{kw}' detected in content.",
        "AI search engines evaluate semantic breadth — not just exact keyword matches.",
        f"Include related terms, subtopics, and entities associated with '{kw}' throughout content.")

def check_topic_depth(page, kw=None):
    depth_signals = {
        "Multiple heading levels (H2+H3)": len(page.h2_tags) > 0 and len(page.h3_tags) > 0,
        "Lists or structured content": page.has_listicles,
        "Tables": page.has_table,
        "Numbered steps": page.has_numbered_steps,
        "Schema markup": len(page.schema_types) > 0,
    }
    score_val = sum(depth_signals.values())
    found_list = [k for k,v in depth_signals.items() if v]
    missing_list = [k for k,v in depth_signals.items() if not v]
    if score_val >= 4:
        return CheckResult("Topic coverage & depth", 3, 3, "pass",
            f"Strong content depth: {', '.join(found_list)}.",
            "Rich content structure signals expertise and improves AI extraction quality.",
            "No action needed.")
    if score_val >= 2:
        return CheckResult("Topic coverage & depth", 2, 3, "warn",
            f"Moderate depth. Present: {', '.join(found_list) or 'none'}. Missing: {', '.join(missing_list)}.",
            "Increasing structural richness improves AI snippet eligibility and user engagement.",
            f"Add: {', '.join(missing_list[:3])}.")
    return CheckResult("Topic coverage & depth", 0, 3, "fail",
        f"Shallow content structure. Missing: {', '.join(missing_list)}.",
        "Content without structure is rarely chosen as an AI answer source.",
        "Add numbered lists, comparison tables, H3 subheadings, and schema markup.")

def check_writing_style(page, kw=None):
    paras = [p for p in page.paragraphs if len(p.split()) > 5]
    if not paras:
        return CheckResult("Clear writing style", 1, 3, "warn",
            "No substantial paragraphs detected to analyse writing style.",
            "AI engines need clear paragraph units to extract answers.",
            "Add clear, well-structured body paragraphs of 50–100 words each.")
    avg = sum(len(p.split()) for p in paras) / len(paras)
    long_p = sum(1 for p in paras if len(p.split()) > 150)
    if avg <= 80 and long_p == 0:
        return CheckResult("Clear writing style", 3, 3, "pass",
            f"Content uses clear, concise paragraphs (avg {avg:.0f} words/paragraph).",
            "Short, focused paragraphs are easily extracted by AI answer engines.",
            "No action needed.")
    if avg <= 120:
        return CheckResult("Clear writing style", 2, 3, "warn",
            f"Writing style is mostly clear but some paragraphs are long (avg {avg:.0f} words).",
            "Overly long paragraphs reduce scannability and AI extractability.",
            "Break paragraphs over 100 words into shorter, focused units.")
    return CheckResult("Clear writing style", 1, 3, "fail",
        f"Paragraphs are too long on average ({avg:.0f} words) — {long_p} very long paragraphs detected.",
        "Dense text blocks are rarely chosen as AI answer sources.",
        "Restructure content into short paragraphs of 50–80 words. One idea per paragraph.")

def check_featured_snippet_format(page, kw=None):
    signals = {
        "Definition-style sentences": page.definition_count >= 2,
        "Bulleted/numbered lists": page.has_listicles,
        "Table present": page.has_table,
        "Short direct answers": page.direct_answer_count >= 3,
        "FAQ section": page.has_faq_section,
    }
    found = [k for k,v in signals.items() if v]
    missing = [k for k,v in signals.items() if not v]
    if len(found) >= 4:
        return CheckResult("Featured snippet format", 3, 3, "pass",
            f"Strong featured snippet formatting: {', '.join(found)}.",
            "Well-formatted content has 30%+ higher chance of being selected as a featured snippet.",
            "No action needed.")
    if len(found) >= 2:
        return CheckResult("Featured snippet format", 2, 3, "warn",
            f"Partial snippet formatting. Present: {', '.join(found) or 'none'}. Missing: {', '.join(missing[:3])}.",
            "More formatting signals improve snippet and AI answer panel eligibility.",
            f"Add: {', '.join(missing[:3])}. Start sections with a direct 1-sentence answer.")
    return CheckResult("Featured snippet format", 0, 3, "fail",
        f"Content lacks specific formatting for featured snippets. Missing: {', '.join(missing)}.",
        "Without snippet-friendly formatting, content rarely appears in position zero or AI overviews.",
        "Add definition sentences, bulleted steps, comparison tables, and concise Q&A pairs.")

def check_answer_friendly(page, kw=None):
    count = page.direct_answer_count
    if count >= 5:
        return CheckResult("Answer-friendly format", 3, 3, "pass",
            f"Content contains {count} direct-answer style sentences — highly AI-extractable.",
            "Direct-answer content is strongly preferred by AI search for generating responses.",
            "No action needed.")
    if count >= 2:
        return CheckResult("Answer-friendly format", 2, 3, "warn",
            f"Content contains {count} direct-answer sentences — could be improved.",
            "More direct answers improve AI extraction and featured snippet eligibility.",
            "Open each section with a 1–2 sentence direct answer before elaborating.")
    return CheckResult("Answer-friendly format", 0, 3, "fail",
        f"Content lacks direct-answer style sentences (found {count}).",
        "AI search engines prefer content that leads sections with concise, direct answers.",
        "Restructure: after each H2 heading, write a direct answer in ≤25 words, then expand.")

def check_long_tail_keywords(page, kw=None):
    if not kw: return None
    long_phrases = re.findall(r'\b[\w][\w\s\-]{20,60}\b', page.full_text)
    kw_words = set(kw.lower().split())
    matching = [p for p in long_phrases if any(w in p.lower() for w in kw_words)]
    if len(matching) >= 5:
        return CheckResult("Use of long-tail keywords", 3, 3, "pass",
            f"The content uses {len(matching)} long-tail keyword phrases related to '{kw}'.",
            "Long-tail phrases capture specific query intent and rank in less competitive searches.",
            "No action needed.")
    return CheckResult("Use of long-tail keywords", 1, 3, "warn",
        f"Limited long-tail keyword variations found for '{kw}'.",
        "Long-tail keywords drive targeted traffic and align with conversational AI queries.",
        f"Add specific sub-topics, questions, and variations of '{kw}' throughout the content.")

# ─────────────────────────── ON-PAGE SEO CHECKS ────────────────────────────

def check_title_length(page, kw=None):
    if not page.title:
        return CheckResult("Title tag length", 0, 3, "fail",
            "No title tag found on this page.",
            "Missing title tag is a critical SEO issue — pages rarely rank without one.",
            "Add <title>Your Keyword – Brand Name</title> inside <head>. 50–60 characters.")
    n = len(page.title)
    details = [f"Found Title: <code>{page.title}</code><br>Length: <strong>{n} characters</strong>"]
    if n < 30:
        return CheckResult("Title tag length", 1, 3, "warn",
            f"Title tag is {n} characters — too short: \"{page.title}\"",
            "Short titles miss keyword and context opportunities.",
            "Expand to 50–60 chars. Include: primary keyword, secondary context, brand name.", details=details)
    if n > 70:
        return CheckResult("Title tag length", 2, 3, "warn",
            f"Title tag is {n} characters — will be truncated in SERPs.",
            "Truncated titles lose tail keywords and reduce SERP listing effectiveness.",
            "Trim to 50–60 chars. Prioritise keyword and value proposition.", details=details)
    return CheckResult("Title tag length", 3, 3, "pass",
        f"Title tag is {n} characters, which is within the 50–70 character optimal range.",
        "Full title will display in SERPs without truncation.",
        "No action needed.", details=details)

def check_description_length(page, kw=None):
    m = page.meta_description
    if not m:
        return CheckResult("Description length", 0, 3, "fail",
            "No meta description found.",
            "Search engines auto-generate snippets — usually poorly — when description is absent.",
            "Add meta description of 120–160 chars with keyword and a clear call-to-action.")
    n = len(m)
    details = [f"Found Description: <code>{m}</code><br>Length: <strong>{n} characters</strong>"]
    if n < 80:
        return CheckResult("Description length", 1, 3, "warn",
            f"Description tag is {n} characters — too short.",
            "Short descriptions waste valuable SERP snippet space.",
            "Expand to 120–160 chars. Describe the page's value and include keyword + CTA.", details=details)
    if n > 165:
        return CheckResult("Description length", 2, 3, "warn",
            f"Description tag is {n} characters — will be truncated.",
            "Truncated descriptions look incomplete in SERPs.",
            "Trim to under 160 chars. Keep the most compelling content first.", details=details)
    return CheckResult("Description length", 3, 3, "pass",
        f"Description tag is {n} characters, which is 160 characters or less.",
        "Description will display fully in search results.",
        "No action needed.", details=details)

def check_heading_structure(page, kw=None):
    h1s = page.h1_tags
    if not h1s:
        return CheckResult("Proper usage of heading tags", 0, 4, "fail",
            "No H1 tag found. H2 and H3 usage cannot be fully evaluated.",
            "Missing H1 is a critical gap — it is the primary on-page keyword signal.",
            "Add exactly one H1 at the top of main content containing your primary keyword.")
    details = []
    if len(h1s) > 1:
        details.append("<strong>Multiple H1s found:</strong>")
        details.extend([f" - <code>{h}</code>" for h in h1s])
        return CheckResult("Proper usage of heading tags", 2, 4, "warn",
            f"{len(h1s)} H1 tags found — there should be exactly one. Found: {', '.join(h1s[:2])}",
            "Multiple H1s dilute topical focus and confuse search engine parsers.",
            "Keep only one H1. Convert extras to H2 or H3.", details=details)
    has_h2 = bool(page.h2_tags)
    has_h3 = bool(page.h3_tags)
    if has_h2 and has_h3:
        return CheckResult("Proper usage of heading tags", 4, 4, "pass",
            f"Heading tags (H1, H2, H3) are used with proper hierarchy. H1: \"{h1s[0][:60]}\"",
            "Correct heading hierarchy helps search engines map content structure.",
            "No action needed.")
    if has_h2:
        details.append("<strong>Missing H3 Tags.</strong> Found H1 and H2s but no H3s.")
        return CheckResult("Proper usage of heading tags", 3, 4, "warn",
            f"H1 and H2 found but no H3 tags. H1: \"{h1s[0][:60]}\"",
            "H3 subheadings improve content granularity and scannability.",
            "Add H3 tags under H2 sections to create deeper content hierarchy.", details=details)
    details.append("<strong>Missing H2 and H3 Tags.</strong>")
    return CheckResult("Proper usage of heading tags", 2, 4, "warn",
        f"Only H1 found — no H2 or H3 tags present. H1: \"{h1s[0][:60]}\"",
        "Without H2/H3, content lacks structure for both users and crawlers.",
        "Add H2 for each major section and H3 for sub-points within sections.", details=details)

def check_alt_tags_present(page, kw=None):
    imgs = page.images
    if not imgs:
        return CheckResult("Image alt Text", 3, 3, "pass",
            "No images found on this page — not applicable.",
            "N/A", "No action needed.")
    with_alt = page.images_with_alt
    pct = len(with_alt) / len(imgs) * 100

    missing_imgs = [img for img in imgs if not img.get("alt", "").strip()]
    details = []
    for m in missing_imgs:
        src = m.get('src', 'No src')
        tag_str = str(m).replace('<', '&lt;').replace('>', '&gt;')
        if len(tag_str) > 150:
            tag_str = tag_str[:147] + "..."
        details.append(f"Missing alt tag for image <strong>{src}</strong><br><code style='color:#c84b2f; background:transparent; padding:0;'>{tag_str}</code>")

    if pct == 100:
        return CheckResult("Image alt Text", 3, 3, "pass",
            f"All {len(imgs)} images have alt text.",
            "Full alt coverage supports accessibility and image search visibility.",
            "No action needed.")
    if pct >= 70:
        return CheckResult("Image alt Text", 2, 3, "warn",
            f"Some image tags are missing alt attributes ({len(with_alt)}/{len(imgs)} have alt, {pct:.0f}%).",
            "Missing alt tags reduce accessibility and image search traffic.",
            "Add descriptive alt text to all images. Include keyword where contextually appropriate.",
            details=details)
    return CheckResult("Image alt Text", 0, 3, "fail",
        f"Only {len(with_alt)}/{len(imgs)} images have alt tags ({pct:.0f}%). Most images are missing alt attributes.",
        "Poor alt coverage is both an accessibility violation and a significant SEO gap.",
        "Add alt attributes to all images. Format: alt='descriptive phrase with keyword if relevant'",
        details=details)

# ─────────────────────────── TECHNICAL CHECKS ──────────────────────────────

def check_seo_friendly_url(page, kw=None):
    slug = page.url_slug or page.url_path.strip("/")
    url_disp = f"/{slug[:60]}"
    details = [f"Evaluated path: <code>{page.url_path}</code>"]
    if re.search(r'[A-Z]', page.url_path):
        return CheckResult("SEO-friendly URL", 1, 3, "warn",
            f"URL contains uppercase characters: {url_disp}",
            "Mixed-case URLs can cause duplicate content issues.",
            "Use all-lowercase URLs. Set up 301 redirects from uppercase variants.", details=details)
    if re.search(r'[^a-z0-9\-/\._~]', page.url_path):
        return CheckResult("SEO-friendly URL", 0, 3, "fail",
            f"URL contains non-SEO-friendly characters: {url_disp}",
            "Special characters in URLs confuse crawlers and reduce link shareability.",
            "Use only lowercase letters, numbers, and hyphens. Remove query strings from canonical URLs.", details=details)
    return CheckResult("SEO-friendly URL", 3, 3, "pass",
        f"URL is clean and uses hyphens: {url_disp or page.url_path[:50] or page.domain}",
        "Clean, readable URLs improve user trust and CTR in SERPs.",
        "No action needed.", details=details)

def check_domain_length(page, kw=None):
    n = page.domain_length
    domain = page.domain
    if n <= 15:
        return CheckResult("Domain length", 3, 3, "pass",
            f"Domain '{domain}' is under 15 characters — concise and memorable.",
            "Short domains are easier to remember, type, and share — supporting brand recall.",
            "No action needed.")
    if n <= 25:
        return CheckResult("Domain length", 2, 3, "warn",
            f"Domain '{domain}' is {n} characters — moderately long.",
            "Longer domains are harder to remember and type accurately.",
            "No action needed for existing sites. Consider a shorter domain for new projects.")
    return CheckResult("Domain length", 1, 3, "warn",
        f"Domain '{domain}' is {n} characters — quite long.",
        "Very long domains reduce brand recall and increase typo risk.",
        "Consider a shorter domain variant for new projects. Existing sites: no action needed.")

def check_ssl(page, kw=None):
    if page.is_https:
        return CheckResult("SSL implementation", 3, 3, "pass",
            "Website uses HTTPS — SSL certificate is active and valid.",
            "HTTPS is a confirmed Google ranking signal and builds user trust.",
            "No action needed.")
    return CheckResult("SSL implementation", 0, 3, "fail",
        "Website is served over HTTP — no SSL certificate detected.",
        "Non-HTTPS sites are flagged as insecure in Chrome and receive a Google ranking penalty.",
        "Install an SSL certificate (free via Let's Encrypt). Redirect all HTTP traffic to HTTPS with 301. Update all internal links.")

def check_robots_txt(page, kw=None):
    if page.has_robots_txt:
        return CheckResult("Robots.txt", 3, 3, "pass",
            "Robots.txt file found and accessible.",
            "Robots.txt guides crawlers to the right pages and protects low-value URLs from indexing.",
            "No action needed. Regularly audit to ensure important pages are not accidentally blocked.")
    return CheckResult("Robots.txt", 0, 3, "fail",
        "No robots.txt file found at the root domain.",
        "Without robots.txt, crawlers may waste budget on admin pages, and you lose control over indexing.",
        "Create /robots.txt. At minimum include: User-agent: * Allow: / Sitemap: https://yourdomain.com/sitemap.xml")

def check_favicon(page, kw=None):
    if page.has_favicon:
        return CheckResult("Favicon", 3, 3, "pass",
            "Favicon is implemented.",
            "Favicons improve brand recognition in browser tabs, bookmarks, and some search results.",
            "No action needed.")
    return CheckResult("Favicon", 0, 3, "warn",
        "No favicon found.",
        "Missing favicon makes the site look unfinished and reduces brand recognition.",
        "Create 32×32 and 180×180 PNG icons. Add <link rel='icon' href='/favicon.ico'> in <head>.")

def check_canonical(page, kw=None):
    if page.canonical:
        details = [f"Found canonical tag: <code>{page.canonical}</code><br>Page URL: <code>{page.final_url}</code>"]
        if page.canonical.rstrip("/") == page.final_url.rstrip("/"):
            return CheckResult("Canonicalization", 3, 3, "pass",
                "Proper canonical URL is set — self-referencing canonical confirmed.",
                "Canonical tags prevent duplicate content dilution across URL variants.",
                "No action needed.", details=details)
        return CheckResult("Canonicalization", 2, 3, "warn",
            f"Canonical tag points to a different URL: {page.canonical[:60]}",
            "Canonical pointing elsewhere transfers ranking signals away from this page.",
            "**Detailed Fix (AI Suggestion):**<br>1. **Verify Intent:** Ensure that you actually want this page to rank. If the canonical points to a different URL, search engines will index *that* URL instead.<br>2. **Update to Self-Reference:** If this page is the original content, update the `href` attribute in your `<link rel='canonical'>` tag to exactly match this page's URL (`https://...`).<br>3. **Check CMS Settings:** In WordPress (Yoast/RankMath) or Shopify, check the advanced SEO settings on this specific page to ensure the canonical URL hasn't been overridden manually.", details=details)
    return CheckResult("Canonicalization", 1, 3, "warn",
        "No canonical tag found on this page.",
        "Without canonicalisation, search engines may index duplicate URL variants (e.g., HTTP vs HTTPS, www vs non-www, or URL parameters).",
        "**Detailed Fix (AI Suggestion):**<br>1. **Add the Tag:** Insert `<link rel='canonical' href='https://yourdomain.com/exact-page-url/'>` into the `<head>` section of your HTML.<br>2. **Dynamic Generation:** Ensure your CMS or framework dynamically generates this tag for every page so it always points to the clean, parameter-free URL.<br>3. **Avoid Duplicates:** Never place more than one canonical tag on a single page, as search engines will ignore both.")

def check_html_sitemap(page, kw=None):
    if page.has_sitemap_html_link:
        return CheckResult("Found a HTML Sitemap", 3, 3, "pass",
            "HTML sitemap link is present on the page.",
            "HTML sitemaps improve navigation and give crawlers an additional discovery path.",
            "No action needed.")
    return CheckResult("Found a HTML Sitemap", 1, 3, "warn",
        "No HTML sitemap link found on this page.",
        "HTML sitemaps help crawlers and users find content that may be buried in navigation.",
        "Create an HTML sitemap page at /sitemap/ and link to it from footer.")

def check_xml_sitemap(page, kw=None):
    if page.has_xml_sitemap:
        return CheckResult("Found a XML Sitemap", 3, 3, "pass",
            "XML sitemap is mentioned in robots.txt and likely present.",
            "XML sitemaps help search engines discover and index all site URLs efficiently.",
            "No action needed. Submit sitemap in Google Search Console.")
    return CheckResult("Found a XML Sitemap", 0, 3, "fail",
        "No XML sitemap reference found in robots.txt.",
        "Without an XML sitemap, search engines may miss new or less-linked pages.",
        "Create /sitemap.xml and reference it in robots.txt: Sitemap: https://yourdomain.com/sitemap.xml")

def check_page_speed(page, kw=None):
    ft = page.fetch_time_ms
    if ft < 800:
        return CheckResult("Page loads fast", 3, 3, "pass",
            f"Page loads quickly (fetched in {ft}ms — fast server response).",
            "Fast pages rank better and reduce bounce rate significantly.",
            "No action needed.")
    if ft < 2000:
        return CheckResult("Page loads fast", 2, 3, "warn",
            f"Page load time is moderate ({ft}ms). Optimisation recommended.",
            "Pages over 1s LCP show increased bounce. Google rewards sub-1s loading.",
            "Optimise: compress images (WebP), enable caching, minify JS/CSS, use CDN.")
    return CheckResult("Page loads fast", 0, 3, "fail",
        f"Page is slow — server responded in {ft}ms. Significant performance issue.",
        "Slow pages are penalised in Core Web Vitals and lose rankings to faster competitors.",
        "Critical: compress images, remove render-blocking scripts, implement server caching, use CDN.")

def check_http_requests(page, kw=None):
    reqs = page.http_requests_approx
    details = [
        f"Images: <strong>{page.image_count}</strong>",
        f"Scripts: <strong>{page.script_count}</strong>",
        f"Stylesheets: <strong>{page.stylesheet_count}</strong>"
    ]
    if reqs < 40:
        return CheckResult("HTTP requests", 3, 3, "pass",
            f"Approx. {reqs} HTTP requests — lean, well-optimised page.",
            "Fewer requests means faster load. Each resource requires a server round trip.",
            "No action needed.", details=details)
    if reqs < 80:
        return CheckResult("HTTP requests", 2, 3, "warn",
            f"Approx. {reqs} HTTP requests — moderate number.",
            "High request counts hurt load time, especially on mobile.",
            "Combine CSS files, use sprites for icons, lazy-load images, defer non-critical JS.", details=details)
    return CheckResult("HTTP requests", 0, 3, "fail",
        f"Approx. {reqs} HTTP requests — excessive.",
        "Too many requests significantly hurt Core Web Vitals and mobile performance.",
        "Audit all resources. Bundle JS/CSS. Lazy-load images. Target under 50 requests.", details=details)

def check_viewport(page, kw=None):
    if page.viewport_meta:
        return CheckResult("Viewport meta tag found", 3, 3, "pass",
            "Viewport meta tag is correctly configured.",
            "Viewport tag enables proper rendering on mobile — essential for Google's mobile-first indexing.",
            "No action needed.")
    return CheckResult("Viewport meta tag found", 0, 3, "fail",
        "No viewport meta tag found.",
        "Without a viewport tag, mobile users see a shrunken desktop version. Google penalises this.",
        "Add <meta name='viewport' content='width=device-width, initial-scale=1'> in <head>.")

def check_mobile_friendly(page, kw=None):
    # Heuristic: viewport + reasonable page size + not excessive inline CSS
    vp = bool(page.viewport_meta)
    reasonable_size = page.page_size_kb < 5000
    low_inline = not page.has_inline_css
    if vp and reasonable_size:
        return CheckResult("Mobile-friendly rendering", 3, 3, "pass",
            "The page appears mobile-friendly based on viewport configuration and page structure.",
            "Mobile-friendliness affects rankings, bounce rate, and Core Web Vitals.",
            "Verify with Google's Mobile-Friendly Test. Ensure tap targets are ≥48px.")
    if vp:
        return CheckResult("Mobile-friendly rendering", 2, 3, "warn",
            "Viewport is set but page size or inline styles may affect mobile experience.",
            "Heavy pages load slowly on mobile networks, hurting engagement and rankings.",
            "Compress images, reduce CSS/JS payload, test with Google Mobile-Friendly Test.")
    return CheckResult("Mobile-friendly rendering", 0, 3, "fail",
        "No viewport meta tag — page is likely not mobile-friendly.",
        "Google uses mobile-first indexing. Non-mobile-friendly pages rank significantly lower.",
        "Add viewport meta tag. Use responsive CSS. Test at search.google.com/test/mobile-friendly")

def check_apple_icon(page, kw=None):
    if page.has_apple_icon:
        return CheckResult("Apple icon found", 3, 3, "pass",
            "Multiple Apple Touch Icons are implemented.",
            "Proper iOS home screen icons improve brand presentation when users bookmark the site.",
            "No action needed.")
    return CheckResult("Apple icon found", 1, 3, "warn",
        "No Apple touch icon found.",
        "Without it, iOS saves a low-quality screenshot as the home screen icon.",
        "Create a 180×180px PNG. Add <link rel='apple-touch-icon' href='/apple-touch-icon.png'>.")

def check_schema(page, kw=None):
    if page.schema_types:
        schema_list = ", ".join(page.schema_types[:6])
        return CheckResult("Schema tags", 3, 3, "pass",
            f"Multiple schema types detected: {schema_list}.",
            "Structured data enables rich results (FAQs, stars, breadcrumbs) improving SERP CTR by 20–30%.",
            "No action needed. Consider adding FAQPage or HowTo schema if not already present.")
    return CheckResult("Schema tags", 0, 3, "fail",
        "No Schema.org structured data detected on this page.",
        "Pages without schema miss eligibility for rich results and AI knowledge panels.",
        "Add JSON-LD schema relevant to your page: Article, FAQPage, Product, LocalBusiness. Validate at search.google.com/test/rich-results")

def check_indexability(page, kw=None):
    if "noindex" in page.robots_meta:
        return CheckResult("Indexability", 0, 3, "fail",
            f"Page has noindex directive: '{page.robots_meta}' — will NOT appear in search results.",
            "This page is completely invisible to all search engines.",
            "Remove 'noindex' from robots meta unless intentional. Submit for indexing in Google Search Console.")
    return CheckResult("Indexability", 3, 3, "pass",
        "No noindex directive found — page is fully indexable.",
        "Page can be crawled and ranked by search engines.",
        "No action needed.")

# ─────────────────────────── AI / GEO CHECKS ───────────────────────────────

def check_faq(page, kw=None):
    if page.has_faq_schema:
        return CheckResult("FAQs", 3, 3, "pass",
            "FAQPage schema markup detected — structured FAQ content found.",
            "FAQ schema enables People Also Ask boxes and AI answer panel inclusion.",
            "No action needed. Ensure answers are concise (under 100 words each).")
    if page.has_faq_section:
        return CheckResult("FAQs", 2, 3, "warn",
            "FAQ section detected in content but no FAQPage schema markup found.",
            "Without schema, FAQ content won't appear in structured rich results.",
            "Add FAQPage JSON-LD schema to your existing FAQ section. Validate at Google Rich Results Test.")
    kw_label = f" for '{kw}'" if kw else ""
    return CheckResult("FAQs", 0, 3, "fail",
        f"No explicit FAQ schema or dedicated FAQ section was found{kw_label}.",
        "FAQ sections are a top signal for AI answer panels and People Also Ask features.",
        "Add a FAQ section with 4–6 Q&A pairs at the bottom of the page. Implement FAQPage schema in JSON-LD.")

def check_summary(page, kw=None):
    if page.has_summary_section:
        return CheckResult("Summary / TL;DR present", 3, 3, "pass",
            "Summary or TL;DR section detected on the page.",
            "Summaries are heavily used by AI engines to generate overview cards and citations.",
            "No action needed. Keep summaries 3–5 bullet points or short sentences.")
    return CheckResult("Summary / TL;DR present", 0, 3, "fail",
        "No summary, TL;DR, or key takeaways section found.",
        "Content without a clear summary is rarely surfaced in AI-generated overviews.",
        "Add a 'Summary' or 'Key Takeaways' section at the top or bottom of your page with 3–5 bullet points.")

def check_readability(page, kw=None):
    score = page.readability_score
    if score == 0:
        return CheckResult("Readability score", 1, 3, "warn",
            "Insufficient text to calculate readability score.",
            "Readable content improves user engagement and AI snippet selection.",
            "Add more content. Aim for Flesch Reading Ease score of 60+ (Grade 8 or below).")
    if score >= 60:
        return CheckResult("Readability score", 3, 3, "pass",
            f"Flesch Reading Ease score: {score:.0f} — easy to read (Grade 8 or below).",
            "Good readability increases AI snippet selection and reduces bounce rate.",
            "No action needed.")
    if score >= 40:
        return CheckResult("Readability score", 2, 3, "warn",
            f"Flesch Reading Ease score: {score:.0f} — moderately complex.",
            "Complex text is less likely to be selected for AI-generated answers.",
            "Simplify sentences (under 20 words), use everyday vocabulary, avoid jargon.")
    return CheckResult("Readability score", 0, 3, "fail",
        f"Flesch Reading Ease score: {score:.0f} — complex text.",
        "Highly complex content is rarely chosen for AI answer extraction.",
        "Rewrite using shorter sentences, plain language, and active voice. Target score 60+.")

def check_internal_links(page, kw=None):
    links = list(set(page.internal_links))
    n = len(links)
    details = [f"Found internal link: <code>{link}</code>" for link in links[:10]]
    if n > 10:
        details.append(f"<em>...and {n - 10} more</em>")
    if n == 0:
        return CheckResult("Helpful internal links", 0, 3, "fail",
            "No internal links detected on this page.",
            "Isolated pages receive less crawl budget and share no authority with the site.",
            "Add at least 5–10 internal links to related pages. Use descriptive keyword anchor text.", details=details if n > 0 else None)
    if n < 5:
        return CheckResult("Helpful internal links", 1, 3, "warn",
            f"Only {n} internal link(s) found — below recommended minimum.",
            "Low internal linking limits PageRank distribution and content discoverability.",
            "Add links to related articles, service pages, and category pages from this content.", details=details)
    return CheckResult("Helpful internal links", 3, 3, "pass",
        f"The page has {n} internal links enhancing content discovery and authority flow.",
        "Strong internal linking distributes PageRank and guides crawlers through your site.",
        "No action needed. Ensure anchor text is descriptive.", details=details)

def check_external_links(page, kw=None):
    links = list(set(page.external_links))
    n = len(links)
    trusted = page.trusted_external_links
    details = [f"Found external link: <code>{link}</code>" for link in links[:10]]
    if n > 10:
        details.append(f"<em>...and {n - 10} more</em>")
    if n == 0:
        return CheckResult("Trusted external links", 1, 3, "warn",
            "No external links found.",
            "Zero outbound links can signal a low-trust, self-contained page to search engines.",
            "Link to 2–4 authoritative external sources (gov, edu, Wikipedia, major publications) to support claims.", details=details if n > 0 else None)
    if trusted > 0:
        return CheckResult("Trusted external links", 3, 3, "pass",
            f"The website links to {trusted} reputable/authoritative source(s) among {n} external links.",
            "Linking to trusted sources signals content quality and boosts topical authority.",
            "No action needed. Ensure all outbound links are relevant and high-quality.", details=details)
    return CheckResult("Trusted external links", 2, 3, "warn",
        f"{n} external links found but none appear to be from highly authoritative domains.",
        "Outbound links to authority sources increase content credibility and trust signals.",
        "Add links to authoritative sources (Wikipedia, government sites, academic papers) to support key claims.", details=details)

def check_voice_search(page, kw=None):
    q_headings = [h for h in page.all_headings if "?" in h]
    details = [f"Found question heading: <code>{h}</code>" for h in q_headings]
    if page.has_voice_search_qa:
        return CheckResult("Voice search ready", 3, 3, "pass",
            "Content includes question-format headings and direct answers suitable for voice search.",
            "Voice search optimisation improves AI assistant citations and featured snippet selection.",
            "No action needed.", details=details)
    if q_headings:
        return CheckResult("Voice search ready", 2, 3, "warn",
            f"Some question-style headings found ({len(q_headings)}) but limited voice-search optimisation.",
            "Voice search requires concise Q&A pairs that can be read aloud in 5–10 seconds.",
            "Add more question headings with direct 1–2 sentence answers beneath each.", details=details)
    return CheckResult("Voice search ready", 1, 3, "warn",
        "Content uses natural language but lacks specific Q&A elements optimized for voice search.",
        "Voice queries are phrased as questions — content without Q&A pairs misses this traffic.",
        "Add 3–5 question-format H3 headings with concise spoken-word-friendly answers below each.")

def check_tone(page, kw=None):
    # Heuristic: check for extreme sentiment words
    text_lower = page.full_text.lower()
    aggressive = ["buy now","limited time","act fast","don't miss","secret","guaranteed"]
    agg_count = sum(1 for w in aggressive if w in text_lower)
    if agg_count > 5:
        return CheckResult("Tone check", 1, 2, "warn",
            "Content contains multiple high-pressure sales phrases.",
            "Overly promotional tone reduces AI citation likelihood and can harm E-E-A-T signals.",
            "Balance promotional language with informational, neutral, helpful content.")
    return CheckResult("Tone check", 2, 2, "pass",
        "The tone appears neutral and informative — appropriate for search visibility.",
        "Neutral, authoritative tone improves E-E-A-T signals and AI citation probability.",
        "No action needed.")

def check_search_intent(page, kw=None):
    if not kw: return None
    kw_lower = kw.lower()
    informational = any(w in kw_lower for w in ["how","what","why","when","which","guide","tips","best","top"])
    transactional = any(w in kw_lower for w in ["buy","price","cheap","deal","order","shop"])
    navigational = any(w in kw_lower for w in ["login","sign in","website","official"])
    full_lower = page.full_text.lower()
    if informational and page.word_count > 500 and len(page.all_headings) > 2:
        return CheckResult("Search intent match", 3, 3, "pass",
            f"The page matches informational search intent for '{kw}' — comprehensive content with structured headings.",
            "Intent-matching content ranks higher and has lower bounce rates.",
            "No action needed.")
    if transactional and (page.schema_types or page.word_count > 300):
        return CheckResult("Search intent match", 3, 3, "pass",
            f"The page appears to match transactional intent for '{kw}'.",
            "Well-matched intent signals improve CTR and conversion rates.",
            "No action needed.")
    return CheckResult("Search intent match", 2, 3, "warn",
        f"Search intent alignment for '{kw}' could be stronger.",
        "Mismatched intent causes high bounce rates and lowers rankings.",
        f"Analyse top-ranking pages for '{kw}' to understand expected content format and depth.")

def check_og_tags(page, kw=None):
    if page.has_og_tags:
        return CheckResult("Open Graph / Social tags", 2, 2, "pass",
            "Open Graph meta tags found — social sharing is optimised.",
            "OG tags control how pages appear when shared on social media, improving CTR from social.",
            "No action needed. Ensure og:image is 1200×630px.")
    return CheckResult("Open Graph / Social tags", 0, 2, "warn",
        "No Open Graph meta tags found.",
        "Without OG tags, social media shares show random content — hurting brand consistency.",
        "Add og:title, og:description, og:image, og:url. Use a 1200×630px image for og:image.")