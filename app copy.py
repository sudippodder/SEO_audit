"""
app.py — AI SEO Audit Tool
Run with:  streamlit run app.py
"""

import os
import time
import json
import validators
import streamlit as st
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

from core import run_audit
from utils.storage import save_audit, get_recent_audits, get_audit_by_id, get_stats, export_csv

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI SEO Audit",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

.main .block-container { max-width: 1100px; padding: 1.5rem 2rem 4rem; }

/* Hero */
.hero-badge {
    display:inline-block; font-family:'Syne',sans-serif; font-size:10px;
    font-weight:700; letter-spacing:0.2em; text-transform:uppercase;
    color:#c84b2f; border:1.5px solid #c84b2f; padding:4px 12px;
    border-radius:2px; margin-bottom:14px;
}
.hero-title {
    font-family:'Syne',sans-serif; font-size:2.4rem; font-weight:800;
    line-height:1.08; letter-spacing:-0.02em; color:#0d0d0d; margin-bottom:8px;
}
.hero-title em { font-style:italic; color:#c84b2f; }
.hero-sub { font-size:0.95rem; color:#6b6660; line-height:1.65; max-width:520px; }

/* Overall score banner */
.score-banner {
    background:#0d0d0d; color:#fff; border-radius:10px;
    padding:1.6rem 2rem; display:flex; align-items:center;
    gap:1.8rem; margin-bottom:1.5rem;
}
.score-num { font-family:'Syne',sans-serif; font-size:4rem; font-weight:800; line-height:1; }
.score-right { display:flex; flex-direction:column; gap:4px; }
.score-eyebrow { font-size:10px; letter-spacing:0.15em; text-transform:uppercase; opacity:0.5; }
.score-grade-red   { font-family:'Syne',sans-serif; font-size:1.25rem; font-weight:700; color:#e07060; }
.score-grade-amber { font-family:'Syne',sans-serif; font-size:1.25rem; font-weight:700; color:#e0b860; }
.score-grade-green { font-family:'Syne',sans-serif; font-size:1.25rem; font-weight:700; color:#60c890; }
.score-domain { font-size:0.82rem; opacity:0.5; margin-top:2px; }
.score-meta-pills { display:flex; flex-wrap:wrap; gap:8px; margin-top:6px; }
.score-pill {
    font-size:11px; padding:3px 10px; border-radius:20px;
    background:rgba(255,255,255,0.1); color:rgba(255,255,255,0.75);
}

/* Module cards */
.module-card {
    background:#fff; border:1.5px solid rgba(13,13,13,0.1);
    border-radius:8px; padding:1.1rem 1.3rem;
    position:relative; overflow:hidden; height:100%;
}
.module-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background:var(--mc,#888);
}
.module-label {
    font-family:'Syne',sans-serif; font-size:10px; font-weight:700;
    letter-spacing:0.12em; text-transform:uppercase; color:#9a9285; margin-bottom:6px;
}
.module-num { font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; line-height:1; color:#0d0d0d; }
.module-bar { height:3px; background:#e8e3d9; border-radius:2px; margin:7px 0; }
.module-fill { height:3px; border-radius:2px; background:var(--mc,#888); }
.mtag { font-size:11px; font-weight:500; padding:2px 8px; border-radius:3px; display:inline-block; }
.mtag-r { background:#fde8e5; color:#c84b2f; }
.mtag-a { background:#fdf3e0; color:#b07010; }
.mtag-g { background:#e4f5ec; color:#1a7a45; }

/* Section label */
.sec-label {
    font-family:'Syne',sans-serif; font-size:10px; font-weight:700;
    letter-spacing:0.15em; text-transform:uppercase; color:#9a9285;
    border-bottom:1px solid rgba(13,13,13,0.1); padding-bottom:8px;
    margin:1.6rem 0 0.9rem;
}

/* Insight cards */
.ins-card {
    background:#fff; border:1.5px solid rgba(13,13,13,0.1);
    border-radius:8px; padding:1rem 1.2rem; margin-bottom:9px;
    display:flex; gap:12px; align-items:flex-start;
}
.ins-icon { font-size:13px; margin-top:2px; flex-shrink:0; }
.ins-title { font-weight:500; font-size:0.88rem; color:#0d0d0d; margin-bottom:3px; }
.ins-finding { font-size:0.82rem; color:#4a4540; line-height:1.55; margin-bottom:4px; }
.ins-impact  { font-size:0.78rem; color:#9a9285; line-height:1.5; font-style:italic; }

/* Detailed audit report — check cards */
.check-card {
    background:#fff; border:1.5px solid rgba(13,13,13,0.08);
    border-radius:8px; padding:1.1rem 1.3rem; margin-bottom:10px;
    border-left:4px solid var(--cc,#ccc);
}
.check-card-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
.check-card-name { font-family:'Syne',sans-serif; font-size:0.88rem; font-weight:700; color:#0d0d0d; }
.check-score-badge {
    font-family:'Syne',sans-serif; font-size:12px; font-weight:700;
    padding:2px 10px; border-radius:3px; background:var(--cc-bg,#f0f0f0); color:var(--cc,#555);
}
.check-status-chip {
    font-size:10px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase;
    padding:2px 8px; border-radius:2px;
}
.chip-fail { background:#fde8e5; color:#c84b2f; }
.chip-warn { background:#fdf3e0; color:#b07010; }
.chip-pass { background:#e4f5ec; color:#1a7a45; }

.check-finding {
    font-size:0.83rem; color:#3a3530; line-height:1.6;
    padding:8px 10px; background:#f5f2ec; border-radius:4px; margin-bottom:8px;
}
.check-impact {
    font-size:0.8rem; color:#6b6660; line-height:1.55; margin-bottom:8px;
}
.fix-box {
    border:1.5px solid rgba(42,138,94,0.25); background:#f0faf5;
    border-radius:6px; padding:10px 12px;
}
.fix-label {
    font-family:'Syne',sans-serif; font-size:9px; font-weight:700;
    letter-spacing:0.15em; text-transform:uppercase; color:#2a8a5e;
    margin-bottom:5px;
}
.fix-text { font-size:0.81rem; color:#1a4a35; line-height:1.6; }

/* Priority fix cards */
.pfix-card {
    background:#fff; border:1.5px solid rgba(13,13,13,0.08);
    border-radius:8px; padding:1rem 1.2rem; margin-bottom:9px;
    display:flex; gap:14px; align-items:flex-start;
}
.pfix-num {
    font-family:'Syne',sans-serif; font-size:1.5rem; font-weight:800;
    color:#e8e3d9; line-height:1; flex-shrink:0; min-width:28px;
}
.pfix-body { flex:1; }
.pfix-name { font-family:'Syne',sans-serif; font-size:0.88rem; font-weight:700; color:#0d0d0d; margin-bottom:3px; }
.pfix-finding { font-size:0.82rem; color:#4a4540; line-height:1.55; margin-bottom:5px; }
.pfix-fix { font-size:0.8rem; color:#2a8a5e; line-height:1.5; }

/* CTA */
.cta-block {
    background:#0d0d0d; border-radius:10px; padding:2.2rem 2rem;
    text-align:center; color:#fff; margin-top:2rem;
}
.cta-eye { font-size:10px; letter-spacing:0.18em; text-transform:uppercase; opacity:0.45; margin-bottom:8px; font-family:'Syne',sans-serif; }
.cta-h { font-family:'Syne',sans-serif; font-size:1.5rem; font-weight:800; margin-bottom:7px; }
.cta-s { font-size:0.88rem; opacity:0.6; line-height:1.65; max-width:420px; margin:0 auto 1.6rem; }

/* Buttons */
div.stButton > button {
    font-family:'Syne',sans-serif !important; font-weight:700 !important;
    letter-spacing:0.06em !important; text-transform:uppercase !important;
    border-radius:4px !important;
}
div.stButton > button[kind="primary"] {
    background:#0d0d0d !important; color:#fff !important;
    border:none !important;
}
div.stButton > button[kind="primary"]:hover { background:#c84b2f !important; }
div.stButton > button[kind="secondary"] {
    background:transparent !important; color:#0d0d0d !important;
    border:1.5px solid rgba(13,13,13,0.25) !important;
}
.stProgress > div > div > div { background-color:#c84b2f !important; }
.stTextInput > div > div > input { border-radius:4px !important; font-family:'DM Sans',sans-serif !important; }
</style>
""", unsafe_allow_html=True)


# ── Helper functions ──────────────────────────────────────────────────────────

MODULE_COLORS = {
    "SEO Foundation":    "#2f6bc8",
    "Content Quality":   "#2a8a5e",
    "AI Visibility":     "#c84b2f",
    "Opportunity Score": "#c8962f",
}

STATUS_COLOR = {"fail": "#c84b2f", "warn": "#c8962f", "pass": "#2a8a5e"}
STATUS_BG    = {"fail": "#fde8e5", "warn": "#fdf3e0", "pass": "#e4f5ec"}
STATUS_CHIP  = {"fail": "chip-fail", "warn": "chip-warn", "pass": "chip-pass"}
STATUS_ICON  = {"fail": "❌", "warn": "⚠️", "pass": "✅"}

FIX_SUGGESTIONS = {
    # SEO Foundation
    "Title tag": {
        "fail": "Add a <title> tag inside your <head>. Write it as: [Primary keyword] – [Brand name]. Keep it 50–60 characters. Example: 'AI SEO Audit Tool – Free Website Checker'.",
        "warn": "Rewrite your title to be 50–60 characters. Include your primary keyword near the front. Avoid keyword stuffing — one clear topic per title.",
    },
    "Meta description": {
        "fail": "Add <meta name='description' content='...'> to your <head>. Write 120–160 characters summarising the page value. Include a call-to-action like 'Learn how…' or 'Discover…'.",
        "warn": "Expand your meta description to 120–160 characters. It should answer: what is this page, why should someone click it, and what will they find?",
    },
    "H1 tag": {
        "fail": "Add exactly one <h1> tag at the top of your content. It should contain your primary keyword and clearly describe what the page is about. Never use more than one H1.",
        "warn": "Remove duplicate H1 tags — keep only one. The remaining H1 should be your most important heading and include your target keyword.",
    },
    "H2 tags": {
        "fail": "Add H2 headings to break your content into sections. Every 200–300 words should have an H2. Use descriptive, keyword-containing phrases.",
        "warn": "Add more H2 headings. Aim for at least one H2 per major topic section. Consider rewriting them as questions to improve AI answer extraction.",
    },
    "Image alt tags": {
        "fail": "Add alt='...' attributes to all <img> tags. Describe what the image shows in 5–10 words. Include your keyword where naturally relevant. Never leave alt empty on informational images.",
        "warn": "Fix the remaining images with missing alt text. Prioritise hero images, product images, and infographics. Decorative images can use alt='' (empty).",
    },
    "Indexability": {
        "fail": "Remove the noindex meta tag from this page unless you intentionally want it hidden. Check for <meta name='robots' content='noindex'> and remove it, then submit the page in Google Search Console.",
    },
    "Internal links": {
        "fail": "Add at least 5–10 internal links to and from this page. Link to related articles, your homepage, and key service pages. Use descriptive anchor text — avoid 'click here'.",
        "warn": "Increase internal links. Add links to related content, cornerstone pages, and your navigation. This distributes authority and helps crawlers find content.",
    },
    # Content Quality
    "Word count": {
        "fail": "Expand content to at least 600–800 words for informational pages. Add context, examples, FAQs, and step-by-step explanations. Thin pages rarely rank for competitive queries.",
        "warn": "Add more depth — aim for 800–1500 words for most pages. Cover related subtopics, add examples, and answer common follow-up questions.",
    },
    "Paragraph size": {
        "fail": "Break your paragraphs into units of 50–80 words maximum. Each paragraph should cover one idea. Short paragraphs improve readability and AI snippet extraction.",
        "warn": "Shorten longer paragraphs. After every 3–4 sentences, start a new paragraph. This helps both human readers and AI models extract your content cleanly.",
    },
    "Heading usage": {
        "fail": "Add headings throughout your content. Use H2 for major sections and H3 for sub-points. Aim for one heading every 200–300 words to structure your content.",
        "warn": "Use headings more consistently. Ensure every major topic has its own H2. Sub-points under each section should use H3.",
    },
    "Content depth signals": {
        "fail": "Add structural depth: use numbered lists (<ol>) for steps, bullet lists for features, and add FAQ schema or How-To schema. These signals show content expertise.",
        "warn": "Increase depth signals by adding schema markup (JSON-LD), numbered steps, or comparison tables. These help search engines classify your content type.",
    },
    # AI Visibility
    "FAQ section": {
        "fail": "Add a FAQ section at the bottom of the page with 4–6 common questions and concise answers. Also implement FAQPage schema (JSON-LD) to make it machine-readable. This is a top signal for AI answer panels.",
        "warn": "Enhance your FAQ section with FAQPage schema markup. Structure each question as <h3> and each answer as <p>. Keep answers under 100 words each.",
    },
    "Summary / TL;DR": {
        "fail": "Add a 2–4 sentence summary at the top or bottom of the page under a heading like 'Summary', 'Key Takeaways', or 'TL;DR'. AI engines use these to generate overview cards.",
        "warn": "Improve your summary section. Make it a standalone block with 3–5 bullet points or short sentences that cover the core message. Put it near the top of the page.",
    },
    "Para length (AI)": {
        "fail": "Rewrite paragraphs to be under 80 words each. AI extraction engines extract paragraph-level chunks. Short, focused paragraphs dramatically improve your chances of being quoted as a source.",
        "warn": "Aim for 60–80 words per paragraph. Split paragraphs that cover more than one idea. Every paragraph should be a self-contained, extractable answer.",
    },
    "Readability": {
        "fail": "Simplify your writing. Use shorter sentences (under 20 words), everyday vocabulary, and active voice. Aim for a Flesch–Kincaid grade of 8 or lower for maximum AI extraction.",
        "warn": "Improve readability by varying sentence length, replacing jargon with plain language, and using subheadings to break up dense text.",
    },
    "Heading structure": {
        "fail": "Rewrite headings as questions or clear topic statements. Examples: 'What is AI SEO?' instead of 'Overview'. 'How to improve your score' instead of 'Score Improvement'. This signals topic relevance to AI engines.",
        "warn": "Make at least 30% of your H2/H3 headings question-style (How, What, Why, Which). These align with how users phrase queries in AI search.",
    },
    "Direct answer sentences": {
        "fail": "Open each section with a direct, concise answer to the implied question in your heading. Example: 'AI SEO is the practice of optimising content for AI-generated answers.' Keep opening sentences under 25 words.",
        "warn": "Add more direct-answer sentences throughout. After each H2 heading, write a 1–2 sentence direct answer before elaborating. This mirrors how AI engines prefer to extract content.",
    },
    "Definition patterns": {
        "fail": "Add definition-style sentences for key terms on the page. Pattern: '[Term] is [definition].' or '[Term] refers to [explanation].' These are heavily used in AI knowledge panels and featured snippets.",
        "warn": "Add 2–3 more definition sentences for key concepts on this page. Use the pattern: 'X is defined as...' or 'X refers to...'. Place them near the start of relevant sections.",
    },
    # Opportunity
    "Critical gaps": {
        "fail": "Address the critical failures first — they have the highest impact. Fix missing title tags, meta descriptions, and noindex issues before optimising anything else.",
        "warn": "Resolve the remaining critical issues. These are foundational elements that block ranking potential regardless of how well other elements are optimised.",
    },
    "Improvement potential": {
        "fail": "A systematic page-by-page SEO audit is needed. Prioritise pages with the most traffic potential and work through each module's fixes in order: SEO Foundation → Content → AI Visibility.",
        "warn": "Create a fix priority list from this report and work through it in sprints. Start with quick wins (15 min or less per fix), then tackle content rewrites.",
    },
    "Quick wins available": {
        "fail": "Implement all quick wins first: add missing meta tags, fix alt text, add a summary section, and implement FAQPage schema. Each of these takes under 30 minutes and directly boosts scores.",
        "warn": "Tackle the remaining quick wins this week. Small fixes compound — even a 10-point improvement in SEO Foundation can meaningfully lift organic traffic.",
    },
}

DEFAULT_FIX = "Review this element against current best practices and update accordingly. Refer to Google's Search Central documentation and the AI visibility guidelines for specific implementation steps."


def get_fix(check_name: str, status: str) -> str:
    fixes = FIX_SUGGESTIONS.get(check_name, {})
    return fixes.get(status) or fixes.get("fail") or DEFAULT_FIX


def grade_color(score: int) -> str:
    if score <= 40: return "red"
    if score <= 70: return "amber"
    return "green"

def tag_html(score: int) -> str:
    label = "Poor" if score <= 40 else ("Average" if score <= 70 else "Strong")
    cls   = "mtag-r" if score <= 40 else ("mtag-a" if score <= 70 else "mtag-g")
    return f'<span class="mtag {cls}">{label}</span>'

def validate_inputs(url: str, email: str) -> dict:
    errors = {}
    if not url.strip():
        errors["url"] = "Please enter a website URL."
    else:
        test = url if url.startswith("http") else "https://" + url
        if not validators.url(test):
            errors["url"] = "Please enter a valid URL, e.g. https://yoursite.com"
    if not email.strip():
        errors["email"] = "Email is required."
    elif not validators.email(email):
        errors["email"] = "Please enter a valid email address."
    return errors


# ── Render functions ──────────────────────────────────────────────────────────

def render_score_banner(report_data: dict, domain: str):
    score  = report_data["overall_score"]
    grade  = report_data["overall_grade"]
    color  = grade_color(score)
    ft     = report_data.get("fetch_time_ms", 0)

    mods = report_data.get("modules", [])
    pills = " ".join(
        f'<span class="score-pill">{m["module"].split()[0]}: {m["score"]}</span>'
        for m in mods
    )

    saved_at = report_data.get("saved_at", "")
    saved_note = f' &nbsp;·&nbsp; Saved {saved_at}' if saved_at else ""

    st.markdown(f"""
    <div class="score-banner">
        <div class="score-num">{score}</div>
        <div class="score-right">
            <span class="score-eyebrow">Overall SEO + AI Score</span>
            <span class="score-grade-{color}">{grade}</span>
            <span class="score-domain">{domain}{saved_note}</span>
            <div class="score-meta-pills">{pills}</div>
        </div>
    </div>""", unsafe_allow_html=True)


def render_module_cards(modules: list):
    cols = st.columns(len(modules))
    for i, m in enumerate(modules):
        c = MODULE_COLORS.get(m["module"], "#888")
        with cols[i]:
            st.markdown(f"""
            <div class="module-card" style="--mc:{c}">
                <div class="module-label">{m['module']}</div>
                <div class="module-num">{m['score']}</div>
                <div class="module-bar">
                    <div class="module-fill" style="width:{m['score']}%"></div>
                </div>
                {tag_html(m['score'])}
            </div>""", unsafe_allow_html=True)


def render_insights(insights: list):
    for ins in insights:
        st.markdown(f"""
        <div class="ins-card">
            <span class="ins-icon">{ins['icon']}</span>
            <div>
                <div class="ins-title">{ins['title']}</div>
                <div class="ins-finding">{ins['finding']}</div>
                <div class="ins-impact">{ins['impact']}</div>
            </div>
        </div>""", unsafe_allow_html=True)


def render_detailed_checks(modules: list):
    """Full detailed audit section — every check with finding + impact + how-to-fix."""
    for mod in modules:
        color = MODULE_COLORS.get(mod["module"], "#888")
        checks = mod.get("checks", [])
        fails  = sum(1 for c in checks if c["status"] == "fail")
        warns  = sum(1 for c in checks if c["status"] == "warn")
        passes = sum(1 for c in checks if c["status"] == "pass")

        header = f"{mod['module']}  —  {mod['score']}/100"
        badge  = f"❌ {fails} failed  ·  ⚠️ {warns} warnings  ·  ✅ {passes} passed"

        with st.expander(f"{header}  ·  {badge}", expanded=(fails > 0)):
            # Module summary bar
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
                <div style="flex:1;height:6px;background:#e8e3d9;border-radius:3px;overflow:hidden;">
                    <div style="height:6px;background:{color};width:{mod['score']}%;border-radius:3px;"></div>
                </div>
                <span style="font-family:'Syne',sans-serif;font-size:12px;font-weight:700;color:{color};">
                    {mod['score']}/100
                </span>
            </div>""", unsafe_allow_html=True)

            # Sort: fails first, then warns, then passes
            sorted_checks = (
                [c for c in checks if c["status"] == "fail"] +
                [c for c in checks if c["status"] == "warn"] +
                [c for c in checks if c["status"] == "pass"]
            )

            for chk in sorted_checks:
                st_color  = STATUS_COLOR.get(chk["status"], "#888")
                st_bg     = STATUS_BG.get(chk["status"], "#f5f5f5")
                chip_cls  = STATUS_CHIP.get(chk["status"], "")
                fix_text  = get_fix(chk["name"], chk["status"])

                st.markdown(f"""
                <div class="check-card" style="--cc:{st_color};--cc-bg:{st_bg};">
                    <div class="check-card-header">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span class="check-status-chip {chip_cls}">{chk['status'].upper()}</span>
                            <span class="check-card-name">{chk['name']}</span>
                        </div>
                        <span class="check-score-badge">{chk['score']}/{chk['max_score']} pts</span>
                    </div>
                    <div class="check-finding">🔍 {chk['finding']}</div>
                    <div class="check-impact">💥 <strong>Impact:</strong> {chk['impact']}</div>
                    {'<div class="fix-box"><div class="fix-label">🔧 How to fix</div><div class="fix-text">' + fix_text + '</div></div>'
                      if chk['status'] in ('fail','warn') else ''}
                </div>""", unsafe_allow_html=True)


def render_priority_fixes(modules: list):
    opp = next((m for m in modules if m["module"] == "Opportunity Score"), None)
    recs = opp.get("top_recommendations", []) if opp else []
    if not recs:
        return

    st.markdown('<div class="sec-label">Priority Fix Plan</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.85rem;color:#6b6660;margin-bottom:12px;">'
        'These are your highest-impact fixes, ranked by score gap. Implement them in order for maximum ROI.</p>',
        unsafe_allow_html=True
    )

    for i, rec in enumerate(recs, 1):
        fix = get_fix(rec["name"], rec["status"])
        icon = STATUS_ICON.get(rec["status"], "•")
        st.markdown(f"""
        <div class="pfix-card">
            <div class="pfix-num">0{i}</div>
            <div class="pfix-body">
                <div class="pfix-name">{icon} {rec['name']}</div>
                <div class="pfix-finding">{rec['finding']}</div>
                <div class="pfix-fix">🔧 {fix}</div>
            </div>
        </div>""", unsafe_allow_html=True)


def render_full_report(report_data: dict):
    """Render a complete audit report from a dict (live or loaded from DB)."""
    url     = report_data.get("url", "")
    domain  = urlparse(url).netloc.replace("www.", "")
    modules = report_data.get("modules", [])
    insights = report_data.get("insights", [])
    error   = report_data.get("error")

    if error:
        st.error(f"**Audit error:** {error}")
        return

    # 1 · Score banner
    render_score_banner(report_data, domain)

    # 2 · Module score cards
    st.markdown('<div class="sec-label">Score Breakdown</div>', unsafe_allow_html=True)
    render_module_cards(modules)

    st.markdown("")

    # Two-column layout: insights left, summary stats right
    left, right = st.columns([3, 2])

    with left:
        # 3 · Key insights
        st.markdown('<div class="sec-label">Key Insights</div>', unsafe_allow_html=True)
        render_insights(insights)

    with right:
        # 4 · Audit stats summary
        st.markdown('<div class="sec-label">Audit Summary</div>', unsafe_allow_html=True)
        all_checks = [c for m in modules for c in m.get("checks", [])]
        total  = len(all_checks)
        fails  = sum(1 for c in all_checks if c["status"] == "fail")
        warns  = sum(1 for c in all_checks if c["status"] == "warn")
        passes = sum(1 for c in all_checks if c["status"] == "pass")

        for label, val, col in [
            ("Total checks run", total, "#0d0d0d"),
            ("❌ Failed", fails, "#c84b2f"),
            ("⚠️ Warnings", warns, "#c8962f"),
            ("✅ Passed", passes, "#2a8a5e"),
        ]:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:9px 12px;background:#fff;border:1.5px solid rgba(13,13,13,0.08);
                        border-radius:6px;margin-bottom:7px;">
                <span style="font-size:0.83rem;color:#4a4540;">{label}</span>
                <span style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:{col};">{val}</span>
            </div>""", unsafe_allow_html=True)

        fetch_ms = report_data.get("fetch_time_ms", 0)
        st.markdown(f"""
        <div style="text-align:center;font-size:11px;color:#9a9285;margin-top:10px;">
            Page fetched in {fetch_ms}ms
        </div>""", unsafe_allow_html=True)

    # 5 · Priority fix plan
    render_priority_fixes(modules)

    # 6 · Full detailed audit (every check, expanded on failures)
    st.markdown('<div class="sec-label">Detailed Audit Report</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.85rem;color:#6b6660;margin-bottom:4px;">'
        'Every check, finding, impact, and how-to-fix instruction. '
        'Sections with failures are expanded by default.</p>',
        unsafe_allow_html=True
    )
    render_detailed_checks(modules)

    # 7 · CTA
    st.markdown("""
    <div class="cta-block">
        <div class="cta-eye">Want expert help?</div>
        <div class="cta-h">Get your complete AI SEO report</div>
        <div class="cta-s">
            This free audit shows the issues. Our full service includes keyword gap analysis,
            competitor benchmarking, content rewrites, and a 30-day implementation plan.
        </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.button("📋  Get Full AI SEO Report", type="primary", use_container_width=True, key=f"cta1_{url[:20]}")
    with col_b:
        st.button("📩  Request Detailed Audit", type="secondary", use_container_width=True, key=f"cta2_{url[:20]}")
    with col_c:
        # JSON download of full report
        st.download_button(
            "⬇️  Download Report JSON",
            data=json.dumps(report_data, indent=2, ensure_ascii=False),
            file_name=f"seo_audit_{domain}.json",
            mime="application/json",
            use_container_width=True,
            key=f"dl_{url[:20]}",
        )


# ── Session state ─────────────────────────────────────────────────────────────
if "report"       not in st.session_state: st.session_state.report       = None
if "show_results" not in st.session_state: st.session_state.show_results = False
if "view_saved"   not in st.session_state: st.session_state.view_saved   = None  # audit_id


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗄️ Audit History")

    stats = get_stats()
    if stats:
        c1, c2 = st.columns(2)
        c1.metric("Audits",      stats.get("total_audits", 0))
        c2.metric("Leads",       stats.get("unique_leads", 0))
        c1.metric("Domains",     stats.get("unique_domains", 0))
        c2.metric("Avg Score",   stats.get("avg_overall", "—"))

    st.divider()

    rows = get_recent_audits(limit=60)
    if rows:
        st.markdown(f"**{len(rows)} saved audits**")

        for r in rows:
            grade_emoji = "🟢" if r["overall_score"] and r["overall_score"] > 70 \
                         else ("🟡" if r["overall_score"] and r["overall_score"] > 40 else "🔴")
            label = f"{grade_emoji} {r['domain'] or r['url'][:30]}  ·  {r['overall_score'] or 'err'}"
            sub   = f"{r['created_at'][:16]}  ·  {r['email']}"
            if st.button(label, key=f"view_{r['id']}", help=sub, use_container_width=True):
                st.session_state.view_saved   = r["id"]
                st.session_state.show_results = False
                st.session_state.report       = None
                st.rerun()

        st.divider()
        csv_data = export_csv()
        if csv_data:
            st.download_button("⬇️ Export leads CSV", data=csv_data,
                               file_name="seo_audit_leads.csv", mime="text/csv",
                               use_container_width=True)
    else:
        st.info("No audits yet. Run your first audit to see history here.")

    if st.session_state.view_saved or st.session_state.show_results:
        st.divider()
        if st.button("← New audit", use_container_width=True):
            st.session_state.show_results = False
            st.session_state.report       = None
            st.session_state.view_saved   = None
            st.rerun()


# ── VIEW SAVED AUDIT ──────────────────────────────────────────────────────────
if st.session_state.view_saved:
    data = get_audit_by_id(st.session_state.view_saved)
    if data:
        domain = urlparse(data.get("url","")).netloc.replace("www.","")
        st.markdown(f'<div class="hero-badge">Saved Audit — {domain}</div>', unsafe_allow_html=True)
        render_full_report(data)
    else:
        st.error("Could not load this audit from the database.")
    st.stop()


# ── HERO ──────────────────────────────────────────────────────────────────────
if not st.session_state.show_results:
    st.markdown('<div class="hero-badge">Free AI SEO Audit</div>', unsafe_allow_html=True)
    st.markdown("""
    <h1 class="hero-title">How visible are you<br>to <em>AI search?</em></h1>
    <p class="hero-sub">Enter your URL and get a full breakdown of your SEO health and AI visibility — with detailed fix instructions for every issue found.</p>
    """, unsafe_allow_html=True)
    st.markdown("---")


# ── FORM ──────────────────────────────────────────────────────────────────────
if not st.session_state.show_results and not st.session_state.view_saved:
    url_input   = st.text_input("Website URL", placeholder="https://yourwebsite.com", key="url_field")
    email_input = st.text_input("Your Email *(required)*", placeholder="you@company.com", key="email_field")

    col1, col2 = st.columns([3, 1])
    with col1:
        run_btn = st.button("🔍  Run AI SEO Audit", type="primary", use_container_width=True)
    with col2:
        st.markdown('<p style="font-size:11px;color:#9a9285;padding-top:10px;">No spam ever.</p>',
                    unsafe_allow_html=True)

    if run_btn:
        errors = validate_inputs(url_input, email_input)
        if errors:
            for _, msg in errors.items():
                st.error(msg)
        else:
            norm_url = url_input if url_input.startswith("http") else "https://" + url_input
            prog = st.progress(0)
            txt  = st.empty()
            steps = [
                (15, "Fetching page content…"),
                (30, "Parsing HTML structure…"),
                (50, "Analysing SEO foundation…"),
                (65, "Checking content quality…"),
                (80, "Evaluating AI visibility signals…"),
                (92, "Calculating opportunity gaps…"),
            ]
            for pct, msg in steps:
                txt.markdown(f"**{msg}**")
                prog.progress(pct)
                time.sleep(0.35)

            report = run_audit(norm_url, email_input)
            save_audit(report)

            prog.progress(100)
            txt.markdown("**Done! Generating your report…**")
            time.sleep(0.3)
            prog.empty(); txt.empty()

            st.session_state.report       = report
            st.session_state.show_results = True
            st.rerun()


# ── LIVE RESULTS ──────────────────────────────────────────────────────────────
if st.session_state.show_results and st.session_state.report:
    report = st.session_state.report
    domain = urlparse(report.url).netloc.replace("www.", "")

    if report.error:
        st.error(f"**Could not audit this URL:** {report.error}")
        st.markdown("Please check the URL is publicly accessible and try again.")
        if st.button("← Try again"):
            st.session_state.show_results = False
            st.session_state.report = None
            st.rerun()
        st.stop()

    # Convert live AuditReport object → dict for unified rendering
    from utils.storage import _report_to_dict
    report_data = _report_to_dict(report)

    st.markdown(f'<div class="hero-badge">Audit Complete — {domain}</div>', unsafe_allow_html=True)
    render_full_report(report_data)

    st.markdown(f"""
    <div style="text-align:center;margin-top:1.5rem;font-size:11px;color:#9a9285;">
        Audited <strong>{domain}</strong> · Scoring is heuristic-based · Results are for guidance only
    </div>""", unsafe_allow_html=True)
