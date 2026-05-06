"""
ai_scorer.py
Scores the AI Visibility module (max 100 pts).
Detects signals that help content appear in AI-generated answers (ChatGPT, Perplexity, SGE, etc.)

Checks:
  FAQ presence                → 20 pts
  Summary / TL;DR presence    → 15 pts
  Paragraph length for AI     → 15 pts
  Readability                 → 15 pts
  Heading structure quality   → 15 pts
  Direct answer sentences     → 10 pts
  Definition patterns         → 10 pts
"""

import re
from .seo_scorer import CheckResult, ModuleResult

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

FAQ_KEYWORDS = [
    "faq", "frequently asked", "common questions", "people also ask",
    "questions and answers", "q&a", "q & a",
]
SUMMARY_KEYWORDS = [
    "summary", "in summary", "in short", "tldr", "tl;dr", "tl dr",
    "to summarize", "in conclusion", "key takeaways", "key points",
    "bottom line", "overview", "in brief", "recap",
]
DIRECT_ANSWER_PATTERNS = [
    r"^(yes|no)[,\.]?\s",          # Starts with Yes/No
    r"^\w[\w\s]{0,30} is\s",       # "X is Y" in short sentence
    r"^\w[\w\s]{0,30} are\s",
    r"^(the|a|an)\s\w",
    r"^(to|you can|you should)\s",
]
DEFINITION_PATTERNS = [
    r"\b\w[\w\s]{1,40}\s+is\s+(a|an|the|defined|described|known|used)",
    r"\b\w[\w\s]{1,40}\s+refers to\b",
    r"\b\w[\w\s]{1,40}\s+means\b",
    r"\bdefin(ition|ed as)\b",
]


def _has_faq(page) -> bool:
    # Check schema types
    if any("faq" in s.lower() for s in page.schema_types):
        return True
    # Check heading text
    for h in page.all_headings:
        if any(kw in h.lower() for kw in FAQ_KEYWORDS):
            return True
    # Check full text
    text_lower = page.full_text.lower()
    return any(kw in text_lower for kw in FAQ_KEYWORDS[:4])


def _has_summary(page) -> bool:
    for h in page.all_headings:
        if any(kw in h.lower() for kw in SUMMARY_KEYWORDS):
            return True
    # Check first/last 500 chars of full text
    snippets = page.full_text[:500].lower() + page.full_text[-500:].lower()
    return any(kw in snippets for kw in SUMMARY_KEYWORDS)


def _count_direct_answer_sentences(page) -> int:
    count = 0
    sentences = re.split(r'(?<=[.!?])\s+', page.full_text)
    for s in sentences:
        s = s.strip()
        if 5 < len(s.split()) < 25:  # concise sentences only
            for pattern in DIRECT_ANSWER_PATTERNS:
                if re.match(pattern, s, re.IGNORECASE):
                    count += 1
                    break
    return count


def _count_definitions(page) -> int:
    count = 0
    for pattern in DEFINITION_PATTERNS:
        count += len(re.findall(pattern, page.full_text, re.IGNORECASE))
    return count


def score(page) -> ModuleResult:
    checks = []
    total = 0

    # ── FAQ presence (20 pts) ────────────────────────────────────────────────
    faq_found = _has_faq(page)
    if faq_found:
        checks.append(CheckResult("FAQ section", 20, 20, "pass",
            "FAQ section or FAQPage schema detected.",
            "FAQ blocks are a top signal for AI-generated direct answers and People Also Ask boxes."))
        total += 20
    else:
        checks.append(CheckResult("FAQ section", 0, 20, "fail",
            "No FAQ section or FAQPage schema detected.",
            "Your page lacks a FAQ section — reducing its chances of appearing in AI-generated answers and featured snippets."))

    # ── Summary / TL;DR (15 pts) ─────────────────────────────────────────────
    summary_found = _has_summary(page)
    if summary_found:
        checks.append(CheckResult("Summary / TL;DR", 15, 15, "pass",
            "Summary or TL;DR section detected.",
            "Summaries are heavily used by AI search engines to generate overview cards."))
        total += 15
    else:
        checks.append(CheckResult("Summary / TL;DR", 0, 15, "fail",
            "No summary or TL;DR section detected.",
            "Content without a clear summary is rarely surfaced in AI-generated overviews. Add a short summary block."))

    # ── Paragraph length for AI (15 pts) ─────────────────────────────────────
    paras = [p for p in page.paragraphs if len(p.split()) > 5]
    if not paras:
        checks.append(CheckResult("Para length (AI)", 5, 15, "warn",
            "No substantial paragraphs found.",
            "AI engines need clear paragraph units to extract answers."))
        total += 5
    else:
        avg = sum(len(p.split()) for p in paras) / len(paras)
        short_paras = sum(1 for p in paras if len(p.split()) <= 80)
        short_ratio = short_paras / len(paras)

        if short_ratio >= 0.7:
            checks.append(CheckResult("Para length (AI)", 15, 15, "pass",
                f"{short_ratio*100:.0f}% of paragraphs are ≤80 words — ideal for AI extraction.",
                "Short, focused paragraphs are easily extracted by AI answer engines."))
            total += 15
        elif short_ratio >= 0.4:
            checks.append(CheckResult("Para length (AI)", 9, 15, "warn",
                f"Only {short_ratio*100:.0f}% of paragraphs are ≤80 words. Avg: {avg:.0f} words.",
                "Break longer paragraphs into shorter units to improve AI extractability."))
            total += 9
        else:
            checks.append(CheckResult("Para length (AI)", 3, 15, "fail",
                f"Most paragraphs are too long for AI extraction. Avg: {avg:.0f} words.",
                "Long dense paragraphs are rarely chosen as AI answer sources. Aim for <80 words per paragraph."))
            total += 3

    # ── Readability (15 pts) ─────────────────────────────────────────────────
    if TEXTSTAT_AVAILABLE and page.full_text and len(page.full_text.split()) > 50:
        try:
            fk_grade = textstat.flesch_kincaid_grade(page.full_text)
            flesch = textstat.flesch_reading_ease(page.full_text)
            if fk_grade <= 8 and flesch >= 60:
                checks.append(CheckResult("Readability", 15, 15, "pass",
                    f"Flesch–Kincaid grade {fk_grade:.1f} — easy to read.",
                    "Good readability increases AI snippet selection and user engagement."))
                total += 15
            elif fk_grade <= 12:
                checks.append(CheckResult("Readability", 9, 15, "warn",
                    f"Flesch–Kincaid grade {fk_grade:.1f} — moderately complex.",
                    "Consider simplifying language for a broader audience and better AI extraction."))
                total += 9
            else:
                checks.append(CheckResult("Readability", 4, 15, "fail",
                    f"Flesch–Kincaid grade {fk_grade:.1f} — complex text.",
                    "Highly complex text is rarely chosen for AI-generated answers. Simplify sentence structures."))
                total += 4
        except Exception:
            checks.append(CheckResult("Readability", 8, 15, "warn",
                "Readability score could not be calculated.",
                "Ensure content is written in clear, plain language."))
            total += 8
    else:
        checks.append(CheckResult("Readability", 8, 15, "warn",
            "Insufficient text to calculate readability.",
            "Add more content to enable readability analysis."))
        total += 8

    # ── Heading structure quality (15 pts) ────────────────────────────────────
    headings = page.all_headings
    if len(headings) == 0:
        checks.append(CheckResult("Heading structure", 0, 15, "fail",
            "No headings found.",
            "Headings are the primary signal AI engines use to understand content topics. This page has none."))
    else:
        # Check if headings contain question-like or keyword-rich patterns
        question_headings = [h for h in headings if "?" in h or
                             any(w in h.lower() for w in ["how", "what", "why", "when", "which", "who", "best", "top"])]
        q_ratio = len(question_headings) / len(headings)

        if q_ratio >= 0.3:
            checks.append(CheckResult("Heading structure", 15, 15, "pass",
                f"{len(question_headings)}/{len(headings)} headings are question-style or keyword-rich.",
                "Question-style headings strongly signal to AI engines what topics are covered."))
            total += 15
        elif len(headings) >= 3:
            checks.append(CheckResult("Heading structure", 9, 15, "warn",
                f"{len(headings)} headings found but few are question-style or keyword-rich.",
                "Rewrite headings as questions or topic phrases to boost AI topic extraction."))
            total += 9
        else:
            checks.append(CheckResult("Heading structure", 5, 15, "warn",
                f"Only {len(headings)} heading(s) — structure is sparse.",
                "Add more descriptive H2/H3 headings to improve AI content understanding."))
            total += 5

    # ── Direct answer sentences (10 pts) ─────────────────────────────────────
    da_count = _count_direct_answer_sentences(page)
    if da_count >= 5:
        checks.append(CheckResult("Direct answer sentences", 10, 10, "pass",
            f"{da_count} direct-answer style sentences detected.",
            "Good — concise, direct sentences are strongly preferred by AI answer extraction."))
        total += 10
    elif da_count >= 2:
        checks.append(CheckResult("Direct answer sentences", 6, 10, "warn",
            f"{da_count} direct-answer sentences detected.",
            "Add more concise, direct sentences that open sections with a clear answer."))
        total += 6
    else:
        checks.append(CheckResult("Direct answer sentences", 0, 10, "fail",
            "Very few direct-answer style sentences found.",
            "AI search favours content that leads sections with a short, direct answer. Restructure key sections accordingly."))

    # ── Definition patterns (10 pts) ─────────────────────────────────────────
    def_count = _count_definitions(page)
    if def_count >= 3:
        checks.append(CheckResult("Definition patterns", 10, 10, "pass",
            f"{def_count} definition-style sentences detected (\"X is…\", \"X refers to…\").",
            "Definition patterns are highly favoured for AI dictionary and knowledge-panel answers."))
        total += 10
    elif def_count >= 1:
        checks.append(CheckResult("Definition patterns", 5, 10, "warn",
            f"{def_count} definition-style sentence(s) found.",
            "Add more clear definitions to improve chances of appearing in knowledge panels."))
        total += 5
    else:
        checks.append(CheckResult("Definition patterns", 0, 10, "fail",
            "No definition patterns detected.",
            "Incorporate sentences in the form 'X is defined as…' to improve AI answer eligibility."))

    max_possible = sum(c.max_score for c in checks)
    normalised = round((total / max_possible) * 100) if max_possible else 0

    return ModuleResult(module="AI Visibility", score=normalised, checks=checks)
