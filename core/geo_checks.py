"""
geo_checks.py
All GEO / AI-specific check functions for the 7 new scoring modules.
Each returns a CheckResult with: name, score, max_score, status, found, impact, how_to_fix.
"""
import re
from dataclasses import dataclass

@dataclass
class CheckResult:
    name: str
    score: int
    max_score: int
    status: str       # pass | warn | fail
    found: str
    impact: str
    how_to_fix: str
    category: str = "GEO"
    effort: str = "medium"   # quick | medium | complex


# ═══════════════════════════════════════════════════════════════════════════
# MODULE 1: AI CITATION READINESS
# Evaluates how ready the page is to be cited by ChatGPT, Gemini, AI Overviews
# ═══════════════════════════════════════════════════════════════════════════

def check_service_definitions(page, kw=None):
    """Clear service/product definitions AI can extract and cite."""
    full = page.full_text.lower()
    def_patterns = [
        r'\b\w[\w\s]{1,30}\s+(is|are|means|refers to|defined as|helps|enables|allows)\b',
        r'\bwe (offer|provide|deliver|specialise|specialize|help)\b',
        r'\bour (service|solution|product|platform|tool|system)\b',
    ]
    count = sum(len(re.findall(p, full, re.I)) for p in def_patterns)
    if count >= 5:
        return CheckResult("Clear service definitions", 4, 4, "pass",
            f"Page contains {count} clear service/product definition statements.",
            "AI systems extract definition-style content to cite your services in answers.",
            "No action needed. Keep definitions concise and factual.")
    if count >= 2:
        return CheckResult("Clear service definitions", 2, 4, "warn",
            f"Only {count} clear service definition statements detected — more needed for AI citation.",
            "AI systems may struggle to clearly understand what your business does or offers.",
            "Add clear 'what we do' statements. Pattern: 'We provide [service] that helps [audience] achieve [outcome].'")
    return CheckResult("Clear service definitions", 0, 4, "fail",
        "No clear service definitions found. AI systems cannot determine what this business offers.",
        "AI systems may struggle to clearly understand your services, reducing citation probability.",
        "Add a clear services section. Use sentences like '[Brand] is a [category] company that [key benefit].' in the first 100 words.")

def check_faq_for_citation(page, kw=None):
    """FAQ presence for AI citation readiness."""
    if page.has_faq_schema:
        return CheckResult("FAQ presence (AI citation)", 4, 4, "pass",
            "FAQPage schema and FAQ section detected — highly AI-citation ready.",
            "FAQs are among the top-cited content formats in ChatGPT, Gemini, and AI Overviews.",
            "No action needed. Ensure answers are under 80 words each for optimal extraction.")
    if page.has_faq_section:
        return CheckResult("FAQ presence (AI citation)", 3, 4, "warn",
            "FAQ content detected but no FAQPage schema markup found.",
            "Without schema, AI crawlers have difficulty identifying and weighting FAQ content.",
            "Wrap your FAQ in FAQPage JSON-LD schema. Validate at Google Rich Results Test.")
    return CheckResult("FAQ presence (AI citation)", 0, 4, "fail",
        "No FAQ section or FAQPage schema found on this page.",
        "Pages without FAQs are rarely cited in AI-generated answers — a major GEO gap.",
        "Add 5–8 Q&A pairs covering common questions about your service. Implement FAQPage schema.")

def check_summary_for_citation(page, kw=None):
    """Summary/TLDR blocks for AI citation."""
    if page.has_summary_section:
        return CheckResult("Summary / TLDR block", 3, 3, "pass",
            "Summary or key takeaways section detected on the page.",
            "AI systems frequently use summary blocks to generate cited overviews.",
            "No action needed. Keep summaries to 3–5 bullet points for best extraction.")
    return CheckResult("Summary / TLDR block", 0, 3, "fail",
        "No summary, TL;DR, or key takeaways block found.",
        "Your pages are not optimized for AI-generated summaries and overviews — AI may skip your content.",
        "Add a 'Key Takeaways' or 'Summary' block at the top of long pages. Use 3–5 bullet points.")

def check_structured_formatting(page, kw=None):
    """Structured formatting signals for AI citation."""
    signals = {
        "Bullet/numbered lists": page.has_listicles,
        "Table": page.has_table,
        "Multiple heading levels": len(page.h2_tags) > 0 and len(page.h3_tags) > 0,
        "Schema markup": len(page.schema_types) > 0,
    }
    found = [k for k,v in signals.items() if v]
    missing = [k for k,v in signals.items() if not v]
    score_val = len(found)
    if score_val >= 3:
        return CheckResult("Structured formatting", 3, 3, "pass",
            f"Good structured formatting detected: {', '.join(found)}.",
            "Structured content is significantly more likely to be extracted and cited by AI systems.",
            "No action needed.")
    if score_val >= 2:
        return CheckResult("Structured formatting", 2, 3, "warn",
            f"Partial formatting: {', '.join(found) or 'none'}. Missing: {', '.join(missing)}.",
            "Your content structure may limit visibility in AI-generated answers.",
            f"Add: {', '.join(missing[:2])}. Use consistent heading hierarchy and list formatting.")
    return CheckResult("Structured formatting", 0, 3, "fail",
        f"Weak content formatting for AI extraction. Missing: {', '.join(missing)}.",
        "Your content structure may limit visibility in AI-generated answers.",
        "Add numbered lists, comparison tables, clear H2/H3 headings, and JSON-LD schema.")

def check_extractable_answers(page, kw=None):
    """Extractable answer-style content."""
    count = page.direct_answer_count
    if count >= 5:
        return CheckResult("Extractable answer-style content", 3, 3, "pass",
            f"{count} direct-answer style sentences detected — highly extractable by AI.",
            "AI systems cite pages that lead sections with concise, direct answers.",
            "No action needed.")
    if count >= 2:
        return CheckResult("Extractable answer-style content", 2, 3, "warn",
            f"Only {count} direct-answer sentences found — below recommended threshold.",
            "Limited extractable content reduces AI citation probability.",
            "Start each major section with a 1–2 sentence direct answer before elaborating.")
    return CheckResult("Extractable answer-style content", 0, 3, "fail",
        "No extractable answer-style content detected.",
        "AI systems may skip your content entirely when generating cited answers.",
        "Rewrite section openers: first sentence should directly answer the implied question in the heading.")


# ═══════════════════════════════════════════════════════════════════════════
# MODULE 2: BRAND / ENTITY CLARITY
# Can AI systems understand who you are, what you do, and your positioning?
# ═══════════════════════════════════════════════════════════════════════════

def check_business_clarity(page, kw=None):
    """Does the page clearly state what the business does?"""
    full = page.full_text.lower()
    clarity_patterns = [
        r'\bwe (are|are a|are an|specialise|specialize|help|serve)\b',
        r'\b(our company|our agency|our firm|our platform|our tool)\b',
        r'\b(founded|established|based in|serving|since \d{4})\b',
    ]
    hits = sum(1 for p in clarity_patterns if re.search(p, full, re.I))
    has_about = any("about" in h.lower() for h in page.all_headings) or "about" in full[:500]
    if hits >= 2 or has_about:
        return CheckResult("Business identity clarity", 3, 3, "pass",
            "Clear business identity signals detected — AI can identify what this entity does.",
            "Entity clarity helps AI systems build an accurate knowledge representation of your brand.",
            "No action needed.")
    if hits == 1:
        return CheckResult("Business identity clarity", 1, 3, "warn",
            "Limited business identity signals — AI may have a partial understanding of your entity.",
            "AI systems may struggle to clearly understand your services.",
            "Add a clear 'About' section or opening paragraph: '[Brand] is a [category] company that [value proposition].'")
    return CheckResult("Business identity clarity", 0, 3, "fail",
        "No clear business identity signals found on this page.",
        "AI systems may struggle to clearly understand your services — reducing citation probability.",
        "Add to your homepage or about page: who you are, what you do, who you serve, and your location/category.")

def check_services_listed(page, kw=None):
    """Are services/products clearly listed?"""
    service_kws = ["service", "solution", "product", "offer", "package", "plan", "feature"]
    full_lower = page.full_text.lower()
    service_hits = sum(full_lower.count(k) for k in service_kws)
    has_service_heading = any(any(k in h.lower() for k in service_kws) for h in page.all_headings)
    has_list = page.has_listicles
    if has_service_heading and has_list:
        return CheckResult("Services / offerings listed", 3, 3, "pass",
            "Services or offerings are listed with a dedicated heading and list formatting.",
            "Clearly listed services help AI build an accurate entity profile for your brand.",
            "No action needed. Consider adding brief descriptions (1 line each) to each service.")
    if service_hits > 3 or has_service_heading:
        return CheckResult("Services / offerings listed", 2, 3, "warn",
            "Services mentioned in text but not clearly listed or structured for AI extraction.",
            "Unstructured service mentions are harder for AI to extract and cite accurately.",
            "Create a dedicated 'Services' or 'What We Offer' section with bulleted or numbered items.")
    return CheckResult("Services / offerings listed", 0, 3, "fail",
        "No clear services or offerings found on this page.",
        "AI systems cannot summarise your business offerings — reducing brand visibility in AI answers.",
        "Add a structured services section: list each service with a name, one-line description, and key benefit.")

def check_industry_category(page, kw=None):
    """Is the industry/category of the business clear?"""
    industry_kws = [
        "industry","sector","market","category","field","space","niche",
        "agency","firm","studio","company","startup","enterprise","consultancy",
        "software","platform","saas","app","tool","service provider"
    ]
    full_lower = page.full_text.lower()
    hits = [k for k in industry_kws if k in full_lower]
    if len(hits) >= 3:
        return CheckResult("Industry / category clarity", 3, 3, "pass",
            f"Industry and category signals detected: {', '.join(hits[:5])}.",
            "Clear industry categorisation helps AI systems place your brand in the right knowledge context.",
            "No action needed.")
    if len(hits) >= 1:
        return CheckResult("Industry / category clarity", 2, 3, "warn",
            f"Partial industry signals found: {', '.join(hits[:3])}. More clarity needed.",
            "Weak category signals make it harder for AI to classify your brand correctly.",
            "Explicitly state your industry: 'We are a [B2B SaaS / digital marketing / fintech] company...'")
    return CheckResult("Industry / category clarity", 0, 3, "fail",
        "No clear industry or category signals detected.",
        "AI systems may misclassify your brand or exclude it from relevant AI-generated answers.",
        "State your industry clearly in the first paragraph. Include category keywords naturally.")

def check_brand_consistency(page, kw=None):
    """Is the brand/business positioning consistent throughout the page?"""
    domain_name = page.domain.split(".")[0].lower()
    full_lower = page.full_text.lower()
    brand_mentions = full_lower.count(domain_name)
    if brand_mentions >= 3:
        return CheckResult("Brand positioning consistency", 3, 3, "pass",
            f"Brand name appears {brand_mentions} times — consistent entity presence throughout content.",
            "Consistent brand mentions reinforce entity recognition across AI knowledge systems.",
            "No action needed.")
    if brand_mentions >= 1:
        return CheckResult("Brand positioning consistency", 2, 3, "warn",
            f"Brand mentioned {brand_mentions} time(s) — more repetition strengthens entity signals.",
            "Weak brand repetition reduces AI entity confidence.",
            "Use your brand name naturally 3–5 times per page. Include in headings, meta, and opening paragraph.")
    return CheckResult("Brand positioning consistency", 0, 3, "warn",
        "Brand name not detected in page content.",
        "AI systems use brand mentions to build entity profiles — absence weakens your AI presence.",
        "Include your brand name naturally in the opening paragraph, at least one heading, and the conclusion.")


# ═══════════════════════════════════════════════════════════════════════════
# MODULE 3: AI EXTRACTABILITY
# How easily can AI systems extract and reuse your content?
# ═══════════════════════════════════════════════════════════════════════════

def check_short_answer_paragraphs(page, kw=None):
    """Short, answer-style paragraphs AI can extract."""
    paras = [p for p in page.paragraphs if len(p.split()) > 5]
    if not paras:
        return CheckResult("Short answer paragraphs", 0, 3, "fail",
            "No substantial paragraphs found for AI extractability analysis.",
            "AI engines cannot extract answers from pages without clear paragraph content.",
            "Add clear body paragraphs of 40–80 words. One idea per paragraph.")
    avg = sum(len(p.split()) for p in paras) / len(paras)
    short = sum(1 for p in paras if len(p.split()) <= 80)
    ratio = short / len(paras)
    if ratio >= 0.7 and avg <= 90:
        return CheckResult("Short answer paragraphs", 3, 3, "pass",
            f"{ratio*100:.0f}% of paragraphs are ≤80 words (avg {avg:.0f} words) — ideal for AI extraction.",
            "Short focused paragraphs are easily lifted verbatim as AI citations.",
            "No action needed.")
    if ratio >= 0.4:
        return CheckResult("Short answer paragraphs", 2, 3, "warn",
            f"Only {ratio*100:.0f}% of paragraphs are ≤80 words. Avg: {avg:.0f} words.",
            "Longer paragraphs reduce AI extraction accuracy and citation likelihood.",
            "Break paragraphs over 100 words into shorter focused units. One idea = one paragraph.")
    return CheckResult("Short answer paragraphs", 0, 3, "fail",
        f"Most paragraphs are too long for AI extraction (avg {avg:.0f} words, {ratio*100:.0f}% under 80 words).",
        "Dense text blocks are rarely extracted or cited by AI systems.",
        "Rewrite: every paragraph should be 40–80 words covering exactly one point.")

def check_definition_content(page, kw=None):
    """Definition-style content for AI knowledge extraction."""
    count = page.definition_count
    if count >= 5:
        return CheckResult("Definition-style content", 3, 3, "pass",
            f"{count} definition-style sentences detected ('X is...', 'X refers to...').",
            "Definitions are the most-cited content format in AI knowledge panels and answer boxes.",
            "No action needed. Ensure definitions are accurate and concise.")
    if count >= 2:
        return CheckResult("Definition-style content", 2, 3, "warn",
            f"Only {count} definition-style sentences found — below AI citation threshold.",
            "Limited definitions reduce your content's eligibility for AI knowledge panels.",
            "Add definitions for key terms: '[Term] is [clear 1-sentence definition].' Aim for 5+ definitions.")
    return CheckResult("Definition-style content", 0, 3, "fail",
        "No definition-style content detected on this page.",
        "AI systems extract definitions to power knowledge panels — no definitions = no panel citations.",
        "Add a terminology or glossary section. Define your core services, methodologies, and key terms.")

def check_structured_lists(page, kw=None):
    """Structured lists for AI scanning and extraction."""
    soup = page.soup
    ul_count = len(soup.find_all("ul")) if soup else 0
    ol_count = len(soup.find_all("ol")) if soup else 0
    li_count = len(soup.find_all("li")) if soup else 0
    if ul_count + ol_count >= 3 and li_count >= 10:
        return CheckResult("Structured lists", 3, 3, "pass",
            f"{ul_count} unordered and {ol_count} ordered lists with {li_count} list items detected.",
            "Lists are among the most extracted content formats in AI-generated answers.",
            "No action needed.")
    if ul_count + ol_count >= 1:
        return CheckResult("Structured lists", 2, 3, "warn",
            f"Only {ul_count + ol_count} list(s) with {li_count} items found — more needed.",
            "Insufficient list content limits AI's ability to extract scannable, citable answers.",
            "Add bulleted lists for benefits, features, steps, and comparisons. Aim for 3+ lists per page.")
    return CheckResult("Structured lists", 0, 3, "fail",
        "No structured lists (UL/OL) found on this page.",
        "Pages without lists are rarely selected for AI bullet-point answers and summaries.",
        "Add at minimum: a benefits list, a features/services list, and a step-by-step process list.")

def check_scannable_formatting(page, kw=None):
    """Is the page scannable for AI and humans?"""
    h2 = len(page.h2_tags); h3 = len(page.h3_tags)
    wc = page.word_count
    heading_density = (h2 + h3) / max(wc / 200, 1) if wc > 0 else 0
    if heading_density >= 0.8 and h2 >= 2:
        return CheckResult("Scannable formatting", 3, 3, "pass",
            f"Good heading density: {h2} H2s and {h3} H3s across {wc} words.",
            "Well-structured scannable pages are preferred by AI for content extraction.",
            "No action needed.")
    if h2 >= 2:
        return CheckResult("Scannable formatting", 2, 3, "warn",
            f"Adequate structure: {h2} H2s, {h3} H3s — but heading frequency could improve.",
            "Sparser headings make it harder for AI to segment and extract topic-specific answers.",
            "Add H2/H3 headings every 200–250 words. Each heading should be a distinct topic.")
    return CheckResult("Scannable formatting", 0, 3, "fail",
        f"Poor scannable structure: only {h2} H2(s) and {h3} H3(s) found.",
        "AI systems struggle to segment and extract content from poorly structured pages.",
        "Add at least 3–4 H2 headings and H3 subheadings. Use descriptive topic-based heading text.")

def check_comparison_content(page, kw=None):
    """Comparison-style formatting for AI extraction."""
    full_lower = page.full_text.lower()
    compare_signals = {
        "vs / versus": bool(re.search(r'\bvs\.?\b|\bversus\b', full_lower)),
        "comparison table": page.has_table,
        "compared to": "compared to" in full_lower or "compared with" in full_lower,
        "pros and cons": "pros" in full_lower and "cons" in full_lower,
        "differences": "difference" in full_lower or "unlike" in full_lower,
    }
    found = [k for k,v in compare_signals.items() if v]
    if len(found) >= 3:
        return CheckResult("Comparison-style content", 3, 3, "pass",
            f"Strong comparison content: {', '.join(found)}.",
            "Comparison content is highly cited in AI responses for 'best X vs Y' queries.",
            "No action needed. Keep comparisons factual and balanced.")
    if len(found) >= 1:
        return CheckResult("Comparison-style content", 2, 3, "warn",
            f"Some comparison signals: {', '.join(found) or 'none'}. More would improve AI extractability.",
            "Limited comparison content reduces visibility for evaluation-intent AI queries.",
            "Add a comparison table or 'X vs Y' section if relevant to your topic.")
    return CheckResult("Comparison-style content", 1, 3, "warn",
        "No comparison-style content detected.",
        "Comparison content is commonly cited in AI answers — its absence is a missed opportunity.",
        "Consider adding a 'How we compare' or 'X vs Y' section with a simple table or bullet list.")


# ═══════════════════════════════════════════════════════════════════════════
# MODULE 4: AI TRUST SIGNALS
# Trust and authority signals important for AI citation confidence
# ═══════════════════════════════════════════════════════════════════════════

def check_testimonials(page, kw=None):
    """Testimonials and social proof."""
    full_lower = page.full_text.lower()
    signals = ["testimonial", "review", "says", "client says", "customer says",
               "★","⭐","rated","rating","stars","what our","what clients"]
    found = [s for s in signals if s in full_lower]
    # Check for blockquotes
    has_blockquote = bool(page.soup.find("blockquote")) if page.soup else False
    if found or has_blockquote:
        return CheckResult("Testimonials / reviews", 3, 3, "pass",
            "Testimonials or review content detected on the page.",
            "Social proof signals increase AI citation confidence and E-E-A-T scores.",
            "No action needed. Add schema markup (Review/AggregateRating) to boost structured data.")
    return CheckResult("Testimonials / reviews", 0, 3, "fail",
        "No testimonials, reviews, or social proof detected.",
        "Limited trust signals may reduce AI citation confidence — AI prefers citing trusted sources.",
        "Add 3–5 client testimonials with name and role. Use Review schema for structured data.")

def check_case_studies(page, kw=None):
    """Case studies and proof of work."""
    full_lower = page.full_text.lower()
    signals = ["case study","case studies","success story","project","results","outcome",
               "achieved","increased","reduced","improved by","grew","roi","% increase","x growth"]
    found = [s for s in signals if s in full_lower]
    has_case_heading = any(any(k in h.lower() for k in ["case study","results","success","project"]) for h in page.all_headings)
    if len(found) >= 3 or has_case_heading:
        return CheckResult("Case studies / proof of results", 3, 3, "pass",
            f"Case study or results content detected: {', '.join(found[:4])}.",
            "Proof of results strengthens E-E-A-T and increases AI citation confidence.",
            "No action needed. Add specific metrics (%, numbers, timeframes) for stronger signals.")
    if len(found) >= 1:
        return CheckResult("Case studies / proof of results", 2, 3, "warn",
            f"Partial results signals: {', '.join(found[:3])}. Dedicated case studies would strengthen trust.",
            "Generic claims without proof reduce AI citation confidence.",
            "Add a dedicated case study or results section with specific metrics and outcomes.")
    return CheckResult("Case studies / proof of results", 0, 3, "fail",
        "No case studies, results data, or proof of work found.",
        "Your content may appear too generic for strong AI visibility — AI avoids citing unsubstantiated claims.",
        "Add a 'Results' or 'Case Studies' section. Include: client type, challenge, solution, measurable outcome.")

def check_about_team(page, kw=None):
    """About/team page signals."""
    full_lower = page.full_text.lower()
    has_about_heading = any("about" in h.lower() or "team" in h.lower() for h in page.all_headings)
    about_signals = ["about us","our team","meet the team","our story","founded","our mission","who we are"]
    has_about = any(s in full_lower for s in about_signals)
    has_team_link = any("about" in l.lower() or "team" in l.lower() for l in page.internal_links)
    if (has_about_heading or has_about) and has_team_link:
        return CheckResult("About / team page", 3, 3, "pass",
            "About/team content and dedicated page link detected.",
            "Author and team transparency significantly boosts E-E-A-T and AI citation confidence.",
            "No action needed. Add LinkedIn profiles and author schema for additional signals.")
    if has_about or has_team_link:
        return CheckResult("About / team page", 2, 3, "warn",
            "Partial about/team signals found but content depth may be insufficient.",
            "Limited team visibility weakens E-E-A-T and reduces AI trust in your content.",
            "Expand about content: add founder story, team bios, years of experience, and mission statement.")
    return CheckResult("About / team page", 0, 3, "fail",
        "No About or Team page content or links detected.",
        "Limited trust signals may reduce AI citation confidence — anonymous content is rarely cited.",
        "Create a detailed About page with team bios, company history, and expertise. Link prominently from homepage.")

def check_trust_badges(page, kw=None):
    """Certifications, awards, trust badges."""
    full_lower = page.full_text.lower()
    trust_signals = [
        "certified","certification","award","awarded","accredited","accreditation",
        "partner","partnership","featured in","as seen in","recognised","recognized",
        "member of","verified","badge","iso","gdpr","ssl","secure"
    ]
    found = [s for s in trust_signals if s in full_lower]
    if len(found) >= 4:
        return CheckResult("Trust badges / certifications", 3, 3, "pass",
            f"Strong trust signals detected: {', '.join(found[:5])}.",
            "Certifications and awards strengthen E-E-A-T signals used by AI to assess content credibility.",
            "No action needed. Add schema markup for awards and certifications.")
    if len(found) >= 2:
        return CheckResult("Trust badges / certifications", 2, 3, "warn",
            f"Some trust signals: {', '.join(found[:3])}. More certifications/badges would strengthen authority.",
            "Limited credentialing signals reduce AI trust assessment scores.",
            "Add industry certifications, partner badges, or media features to the page.")
    return CheckResult("Trust badges / certifications", 0, 3, "fail",
        "No trust badges, certifications, or authority signals detected.",
        "Limited trust signals may reduce AI citation confidence significantly.",
        "Display relevant certifications, industry memberships, partner logos, or media mentions with schema markup.")

def check_contact_transparency(page, kw=None):
    """Contact information transparency."""
    full_lower = page.full_text.lower()
    contact_signals = ["contact","phone","email","address","location","office","reach us","get in touch"]
    found = [s for s in contact_signals if s in full_lower]
    has_contact_link = any("contact" in l.lower() for l in page.internal_links)
    has_phone = bool(re.search(r'\b(\+?\d[\d\s\-\(\)]{7,15})\b', page.full_text))
    has_email_pattern = bool(re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', page.full_text))
    score_signals = sum([bool(found), has_contact_link, has_phone, has_email_pattern])
    if score_signals >= 3:
        return CheckResult("Contact transparency", 3, 3, "pass",
            "Contact information and links are clearly present and accessible.",
            "Contact transparency is a key E-E-A-T signal — AI systems prefer citing contactable businesses.",
            "No action needed. Add LocalBusiness schema for additional structured data.")
    if score_signals >= 1:
        return CheckResult("Contact transparency", 2, 3, "warn",
            f"Partial contact information found. Improve accessibility: {', '.join(found[:3])}.",
            "Incomplete contact visibility weakens trust signals for AI systems.",
            "Add full contact details: phone, email, physical address (if applicable), and a Contact page link.")
    return CheckResult("Contact transparency", 0, 3, "fail",
        "No contact information found on this page.",
        "Anonymous pages are assigned lower trust by AI systems — reducing citation probability.",
        "Add a visible contact section or footer with email, phone, and a link to your contact page.")


# ═══════════════════════════════════════════════════════════════════════════
# MODULE 5: AI OVERVIEW READINESS
# Readiness for AI-generated summaries and answer overviews
# ═══════════════════════════════════════════════════════════════════════════

def check_qa_formatting(page, kw=None):
    """Question-answer formatting for AI overview readiness."""
    q_headings = [h for h in page.all_headings if "?" in h]
    if len(q_headings) >= 4:
        return CheckResult("Question-answer formatting", 3, 3, "pass",
            f"{len(q_headings)} question-format headings detected — strong AI overview signal.",
            "Q&A formatted content is the primary format cited in Google AI Overviews and ChatGPT answers.",
            "No action needed. Ensure each question heading has a direct 1–2 sentence answer below it.")
    if len(q_headings) >= 2:
        return CheckResult("Question-answer formatting", 2, 3, "warn",
            f"Only {len(q_headings)} question-format headings found — more needed for AI overview readiness.",
            "Insufficient Q&A formatting reduces eligibility for AI-generated summaries.",
            "Add 4–6 question-format H2/H3 headings with concise answers below each.")
    return CheckResult("Question-answer formatting", 0, 3, "fail",
        "No question-format headings found on this page.",
        "Your pages are not optimized for AI-generated summaries and overviews.",
        "Add questions as H2/H3 headings (e.g. 'What is [service]? How does [process] work?') with direct answers.")

def check_informational_structure(page, kw=None):
    """Informational content structure for AI overviews."""
    has_intro = len(page.paragraphs) > 0 and len(page.paragraphs[0].split()) >= 30
    has_sections = len(page.h2_tags) >= 2
    has_conclusion = page.has_summary_section
    has_depth = page.word_count >= 500
    signals = {"Clear introduction": has_intro, "Multiple sections (H2)": has_sections,
               "Conclusion/summary": has_conclusion, "Sufficient depth (500+ words)": has_depth}
    found = [k for k,v in signals.items() if v]
    missing = [k for k,v in signals.items() if not v]
    if len(found) >= 3:
        return CheckResult("Informational content structure", 3, 3, "pass",
            f"Strong informational structure: {', '.join(found)}.",
            "Well-structured informational pages are preferred for AI overview generation.",
            "No action needed.")
    if len(found) >= 2:
        return CheckResult("Informational content structure", 2, 3, "warn",
            f"Partial structure: {', '.join(found)}. Missing: {', '.join(missing)}.",
            "Incomplete informational structure reduces AI overview eligibility.",
            f"Add: {', '.join(missing[:2])}.")
    return CheckResult("Informational content structure", 0, 3, "fail",
        f"Weak informational structure. Missing: {', '.join(missing)}.",
        "Your content structure may limit visibility in AI-generated answers.",
        "Add: clear intro paragraph, 3+ H2 sections, summary/conclusion, and expand word count to 600+.")

def check_snippet_friendly(page, kw=None):
    """Snippet-friendly formatting."""
    paras = [p for p in page.paragraphs if 20 <= len(p.split()) <= 60]
    snippet_paras = len(paras)
    has_bold = bool(page.bold_italic_text.strip())
    has_lists = page.has_listicles
    score_val = sum([snippet_paras >= 3, has_bold, has_lists])
    if score_val >= 3:
        return CheckResult("Snippet-friendly formatting", 3, 3, "pass",
            f"Strong snippet formatting: {snippet_paras} snippet-length paragraphs, bold text, lists.",
            "Snippet-optimised content is directly selected for AI overview cards and featured snippets.",
            "No action needed.")
    if score_val >= 2:
        return CheckResult("Snippet-friendly formatting", 2, 3, "warn",
            f"Partial snippet formatting: {snippet_paras} short paragraphs, bold: {has_bold}, lists: {has_lists}.",
            "Incomplete snippet optimisation reduces selection probability for AI overview cards.",
            "Add bold text for key terms, ensure key paragraphs are 20–60 words, add bulleted summaries.")
    return CheckResult("Snippet-friendly formatting", 0, 3, "fail",
        "Poor snippet-friendly formatting detected.",
        "Your pages are not optimized for AI-generated summaries and overviews.",
        "Create snippet-worthy paragraphs (20–60 words), add bold key terms, and include bullet summaries.")

def check_concise_factual(page, kw=None):
    """Concise factual explanations for AI overviews."""
    sents = re.split(r'(?<=[.!?])\s+', page.full_text)
    concise_factual = [s for s in sents if 10 <= len(s.split()) <= 30
                       and re.search(r'\b(is|are|was|were|provides|offers|enables|helps)\b', s, re.I)]
    count = len(concise_factual)
    if count >= 8:
        return CheckResult("Concise factual explanations", 3, 3, "pass",
            f"{count} concise factual sentences detected — strong AI overview material.",
            "Concise factual sentences are the primary building blocks of AI-generated overviews.",
            "No action needed.")
    if count >= 4:
        return CheckResult("Concise factual explanations", 2, 3, "warn",
            f"Only {count} concise factual sentences found — below recommended threshold for AI overviews.",
            "Insufficient factual density limits AI overview selection probability.",
            "Add more 10–30 word factual statements. Each should be independently meaningful.")
    return CheckResult("Concise factual explanations", 0, 3, "fail",
        f"Very few concise factual explanations found ({count} detected).",
        "Your pages are not optimized for AI-generated summaries and overviews.",
        "Rewrite key content sections as standalone factual sentences. Avoid vague or flowery language.")


# ═══════════════════════════════════════════════════════════════════════════
# MODULE 6: INFORMATION GAIN / ORIGINALITY
# Is content original, specific, and differentiating — or generic?
# ═══════════════════════════════════════════════════════════════════════════

def check_generic_copy(page, kw=None):
    """Detect generic, boilerplate service copy."""
    generic_phrases = [
        "we are passionate about","world-class","cutting-edge","state-of-the-art",
        "one-stop","holistic","synergy","leverage","streamline","seamlessly",
        "innovative solutions","trusted partner","comprehensive solutions",
        "best in class","leading provider","industry-leading"
    ]
    full_lower = page.full_text.lower()
    found = [p for p in generic_phrases if p in full_lower]
    if len(found) <= 1:
        return CheckResult("Generic service copy", 3, 3, "pass",
            "Content appears specific and differentiated — minimal generic filler phrases detected.",
            "Original, specific content is more likely to be cited by AI than generic copy.",
            "No action needed. Continue using specific, evidence-backed language.")
    if len(found) <= 4:
        return CheckResult("Generic service copy", 2, 3, "warn",
            f"Some generic phrases detected: {', '.join(found[:4])}.",
            "Your content may appear too generic for strong AI visibility.",
            f"Replace generic phrases with specific claims: instead of 'world-class service', say 'rated 4.9/5 by 200+ clients'.")
    return CheckResult("Generic service copy", 0, 3, "fail",
        f"High concentration of generic copy detected ({len(found)} phrases): {', '.join(found[:5])}.",
        "Your content may appear too generic for strong AI visibility — AI deprioritises boilerplate content.",
        "Replace all generic filler with specific claims, results, and differentiators. Every sentence should contain a concrete detail.")

def check_thin_content(page, kw=None):
    """Thin content detection."""
    wc = page.word_count
    unique_ratio = len(set(page.full_text.lower().split())) / max(wc, 1)
    if wc >= 800 and unique_ratio >= 0.4:
        return CheckResult("Content depth / thin content", 3, 3, "pass",
            f"Good content depth: {wc} words with vocabulary richness ratio of {unique_ratio:.2f}.",
            "Substantive, vocabulary-rich content signals expertise and improves AI citation probability.",
            "No action needed.")
    if wc >= 400:
        return CheckResult("Content depth / thin content", 2, 3, "warn",
            f"Moderate content depth: {wc} words. Vocabulary richness: {unique_ratio:.2f}.",
            "Thin content is deprioritised by AI systems for answer generation.",
            "Expand content to 800+ words. Add specific examples, data points, and detailed explanations.")
    return CheckResult("Content depth / thin content", 0, 3, "fail",
        f"Thin content detected: only {wc} words. Vocabulary richness: {unique_ratio:.2f}.",
        "Your content may appear too generic for strong AI visibility — AI avoids citing thin pages.",
        "Expand significantly: add examples, statistics, step-by-step explanations, FAQs, and case study snippets.")

def check_examples_proof(page, kw=None):
    """Examples, data, and proof presence."""
    full_lower = page.full_text.lower()
    proof_signals = {
        "Statistics/numbers": bool(re.search(r'\b\d+(\.\d+)?%|\d+ (clients|users|companies|customers|projects)\b', page.full_text)),
        "Examples": "for example" in full_lower or "such as" in full_lower or "e.g." in full_lower,
        "Case evidence": "result" in full_lower or "achieved" in full_lower or "outcome" in full_lower,
        "Data references": bool(re.search(r'\b(study|research|survey|report|data|according to)\b', full_lower)),
    }
    found = [k for k,v in proof_signals.items() if v]
    missing = [k for k,v in proof_signals.items() if not v]
    if len(found) >= 3:
        return CheckResult("Examples and proof", 3, 3, "pass",
            f"Strong evidence detected: {', '.join(found)}.",
            "Evidence-backed content has significantly higher AI citation rates.",
            "No action needed. Add specific metrics wherever possible.")
    if len(found) >= 2:
        return CheckResult("Examples and proof", 2, 3, "warn",
            f"Partial evidence: {', '.join(found)}. Missing: {', '.join(missing)}.",
            "Insufficient proof signals reduce content credibility in AI eyes.",
            f"Add: {', '.join(missing)}. Include specific numbers and real examples.")
    return CheckResult("Examples and proof", 0, 3, "fail",
        f"No concrete evidence, examples, or data found. Missing: {', '.join(missing)}.",
        "Your content may appear too generic for strong AI visibility — claims without proof are rarely cited.",
        "Add: specific statistics, client examples, before/after data, or research citations.")

def check_unique_insights(page, kw=None):
    """Unique insights and original perspective."""
    full_lower = page.full_text.lower()
    insight_signals = [
        "our approach","our methodology","our framework","we believe","our philosophy",
        "unique","proprietary","our process","how we","what makes us","unlike others",
        "our experience","we've found","in our experience","based on"
    ]
    found = [s for s in insight_signals if s in full_lower]
    if len(found) >= 4:
        return CheckResult("Unique insights / original perspective", 3, 3, "pass",
            f"Strong original perspective signals: {', '.join(found[:5])}.",
            "Unique insights differentiate content from generic results — improving AI citation preference.",
            "No action needed. Continue sharing proprietary methods and original perspectives.")
    if len(found) >= 2:
        return CheckResult("Unique insights / original perspective", 2, 3, "warn",
            f"Some unique signals: {', '.join(found[:3])}. Deeper original perspective needed.",
            "Lack of unique insights makes content interchangeable with competitors — reducing AI preference.",
            "Share your methodology, lessons learned, or data-backed opinions. 'We believe X because [evidence].'")
    return CheckResult("Unique insights / original perspective", 0, 3, "fail",
        "No unique insights or original perspective signals detected.",
        "Your content may appear too generic for strong AI visibility — AI prefers authoritative, original sources.",
        "Add a 'Our Approach' or 'Our Perspective' section. Share specific processes, opinions, or proprietary frameworks.")


# ═══════════════════════════════════════════════════════════════════════════
# MODULE 7: GEO OPPORTUNITY SCORE
# Identifies missed AI visibility opportunities — creates curiosity for consultation
# ═══════════════════════════════════════════════════════════════════════════

def compute_geo_opportunity(citation_score, entity_score, extractability_score,
                             trust_score, overview_score, originality_score, seo_score):
    """
    GEO Opportunity Score = inverse gap score.
    Higher gap = lower score = more opportunity = more reason to consult.
    """
    scores = [citation_score, entity_score, extractability_score,
              trust_score, overview_score, originality_score]
    avg_geo = sum(scores) / len(scores)
    # Opportunity = how far from 100 across all GEO modules
    gap = 100 - avg_geo
    checks = []

    # Missing AI-friendly sections
    if citation_score < 60:
        checks.append(CheckResult("AI-friendly sections missing", 0, 3, "fail",
            f"AI Citation Readiness score is {citation_score}/100 — critical gaps in AI-optimised content.",
            "Missing AI-friendly sections significantly reduce your chances of appearing in AI-generated answers.",
            "Prioritise: FAQ section, Summary block, and Service definitions. These have the highest GEO impact."))
    else:
        checks.append(CheckResult("AI-friendly sections", 3, 3, "pass",
            f"AI Citation Readiness score of {citation_score}/100 — AI-friendly sections present.",
            "Core AI citation elements are in place.",
            "Continue refining and expanding AI-optimised content."))

    if extractability_score < 60:
        checks.append(CheckResult("AI extractability gaps", 0, 3, "fail",
            f"AI Extractability score is {extractability_score}/100 — content is difficult for AI to extract.",
            "Weak extractability means AI systems will skip your content when generating answers.",
            "Add short paragraphs, definition sentences, structured lists, and comparison tables."))
    else:
        checks.append(CheckResult("AI extractability", 3, 3, "pass",
            f"AI Extractability score of {extractability_score}/100 — content is extractable.",
            "Content structure supports AI extraction.",
            "Maintain current formatting and continue improving."))

    if trust_score < 60:
        checks.append(CheckResult("Trust signal gaps", 0, 3, "fail",
            f"AI Trust Signals score is {trust_score}/100 — insufficient authority signals.",
            "Limited trust signals may reduce AI citation confidence — AI prefers citing established, verifiable sources.",
            "Add testimonials, case studies, team bios, certifications, and contact transparency."))
    else:
        checks.append(CheckResult("Trust signals", 3, 3, "pass",
            f"Trust signals score of {trust_score}/100 — adequate authority presence.",
            "Trust signals support AI citation confidence.",
            "Continue building trust through case studies and testimonials."))

    if overview_score < 60:
        checks.append(CheckResult("AI overview readiness gaps", 0, 3, "fail",
            f"AI Overview Readiness score is {overview_score}/100 — not optimised for AI summary generation.",
            "Your pages are not optimized for AI-generated summaries and overviews.",
            "Add Q&A headings, snippet-friendly paragraphs, and concise factual statements throughout content."))
    else:
        checks.append(CheckResult("AI overview readiness", 3, 3, "pass",
            f"AI Overview Readiness score of {overview_score}/100 — adequate overview preparation.",
            "Content is positioned for AI overview inclusion.",
            "Continue adding Q&A sections and snippet-optimised paragraphs."))

    if originality_score < 60:
        checks.append(CheckResult("Content originality gaps", 0, 3, "fail",
            f"Information Gain score is {originality_score}/100 — content appears too generic.",
            "Your content may appear too generic for strong AI visibility — AI deprioritises commodity content.",
            "Add specific data, unique insights, real examples, and proprietary perspectives."))
    else:
        checks.append(CheckResult("Content originality", 3, 3, "pass",
            f"Content Originality score of {originality_score}/100 — differentiated content detected.",
            "Original content is preferred by AI citation systems.",
            "Continue differentiating with proprietary data and unique perspectives."))

    # Overall opportunity
    total = sum(c.score for c in checks)
    mx = sum(c.max_score for c in checks)
    norm = round(total / mx * 100) if mx else 0

    from dataclasses import dataclass, field
    from typing import List

    @dataclass
    class GeoOpportunityResult:
        module: str
        score: int
        checks: List[CheckResult]
        gap_score: float  # How much opportunity exists (100 - avg_geo)

    return GeoOpportunityResult(
        module="GEO Opportunity Score",
        score=norm,
        checks=checks,
        gap_score=round(gap, 1)
    )