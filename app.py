"""app.py — AI SEO Audit Tool  |  streamlit run app.py"""
import os, time, json, validators
import streamlit as st
from dotenv import load_dotenv
from urllib.parse import urlparse
load_dotenv()

from core import run_audit
from utils.storage import save_audit, get_recent_audits, get_audit_by_id, get_stats, export_csv, _report_to_dict

st.set_page_config(page_title="AI SEO Audit", page_icon="🔍", layout="wide", initial_sidebar_state="expanded")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.main .block-container{max-width:1080px;padding:1.5rem 2rem 4rem;}

/* Hero */
.hero-badge{display:inline-block;font-family:'Syne',sans-serif;font-size:10px;font-weight:700;
 letter-spacing:.2em;text-transform:uppercase;color:#c84b2f;border:1.5px solid #c84b2f;
 padding:4px 12px;border-radius:2px;margin-bottom:14px;}
.hero-title{font-family:'Syne',sans-serif;font-size:2.4rem;font-weight:800;line-height:1.08;
 letter-spacing:-.02em;color:#0d0d0d;margin-bottom:8px;}
.hero-title em{font-style:italic;color:#c84b2f;}
.hero-sub{font-size:.95rem;color:#6b6660;line-height:1.65;max-width:560px;}

/* Score banner */
.score-banner{background:#0d0d0d;color:#fff;border-radius:10px;padding:1.6rem 2rem;
 display:flex;align-items:center;gap:2rem;margin-bottom:1.5rem;flex-wrap:wrap;}
.score-big{font-family:'Syne',sans-serif;font-size:4rem;font-weight:800;line-height:1;}
.score-right{display:flex;flex-direction:column;gap:4px;}
.score-eye{font-size:10px;letter-spacing:.15em;text-transform:uppercase;opacity:.5;}
.sg-r{font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:700;color:#e07060;}
.sg-a{font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:700;color:#e0b860;}
.sg-g{font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:700;color:#60c890;}
.score-sub{font-size:.82rem;opacity:.5;margin-top:2px;}
/* Two score pills */
.score-pair{display:flex;gap:12px;flex-wrap:wrap;}
.score-pill-box{background:rgba(255,255,255,.08);border-radius:8px;padding:.8rem 1.2rem;text-align:center;min-width:100px;}
.pill-num{font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;line-height:1;}
.pill-label{font-size:10px;letter-spacing:.1em;text-transform:uppercase;opacity:.55;margin-top:2px;}

/* Section label */
.sec-label{font-family:'Syne',sans-serif;font-size:10px;font-weight:700;letter-spacing:.15em;
 text-transform:uppercase;color:#9a9285;border-bottom:1px solid rgba(13,13,13,.1);
 padding-bottom:8px;margin:1.6rem 0 .9rem;}

/* Insight card */
.ins-card{background:#fff;border:1.5px solid rgba(13,13,13,.1);border-radius:8px;
 padding:1rem 1.2rem;margin-bottom:9px;display:flex;gap:12px;align-items:flex-start;}
.ins-title{font-weight:500;font-size:.88rem;color:#0d0d0d;margin-bottom:3px;}
.ins-found{font-size:.82rem;color:#4a4540;line-height:1.55;margin-bottom:4px;}
.ins-impact{font-size:.78rem;color:#9a9285;line-height:1.5;font-style:italic;}

/* Check card */
.chk-card{background:#fff;border:1.5px solid rgba(13,13,13,.08);border-radius:8px;
 padding:1.1rem 1.3rem;margin-bottom:10px;border-left:4px solid var(--cc,#ccc);}
.chk-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;}
.chk-name{font-family:'Syne',sans-serif;font-size:.87rem;font-weight:700;color:#0d0d0d;}
.chk-badge{font-family:'Syne',sans-serif;font-size:11px;font-weight:700;
 padding:2px 10px;border-radius:3px;background:var(--cc-bg,#f0f0f0);color:var(--cc,#555);}
.chip{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:2px 8px;border-radius:2px;}
.chip-f{background:#fde8e5;color:#c84b2f;}.chip-w{background:#fdf3e0;color:#b07010;}.chip-p{background:#e4f5ec;color:#1a7a45;}
.found-box{font-size:.83rem;color:#3a3530;line-height:1.6;padding:8px 10px;background:#f5f2ec;border-radius:4px;margin-bottom:8px;}
.impact-box{font-size:.8rem;color:#6b6660;line-height:1.55;margin-bottom:8px;}
.fix-box{border:1.5px solid rgba(42,138,94,.25);background:#f0faf5;border-radius:6px;padding:10px 12px;}
.fix-lbl{font-family:'Syne',sans-serif;font-size:9px;font-weight:700;letter-spacing:.15em;
 text-transform:uppercase;color:#2a8a5e;margin-bottom:5px;}
.fix-txt{font-size:.81rem;color:#1a4a35;line-height:1.6;}

/* Stats row */
.stat-box{background:#fff;border:1.5px solid rgba(13,13,13,.08);border-radius:6px;
 padding:9px 12px;margin-bottom:7px;display:flex;justify-content:space-between;align-items:center;}
.stat-val{font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;}

/* CTA */
.cta-block{background:#0d0d0d;border-radius:10px;padding:2.2rem 2rem;text-align:center;color:#fff;margin-top:2rem;}
.cta-eye{font-size:10px;letter-spacing:.18em;text-transform:uppercase;opacity:.45;margin-bottom:8px;font-family:'Syne',sans-serif;}
.cta-h{font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;margin-bottom:7px;}
.cta-s{font-size:.88rem;opacity:.6;line-height:1.65;max-width:420px;margin:0 auto 1.6rem;}

/* Buttons */
div.stButton>button{font-family:'Syne',sans-serif!important;font-weight:700!important;
 letter-spacing:.06em!important;text-transform:uppercase!important;border-radius:4px!important;}
div.stButton>button[kind="primary"]{background:#0d0d0d!important;color:#fff!important;border:none!important;}
div.stButton>button[kind="primary"]:hover{background:#c84b2f!important;}
div.stButton>button[kind="secondary"]{background:transparent!important;color:#0d0d0d!important;border:1.5px solid rgba(13,13,13,.25)!important;}
.stProgress>div>div>div{background-color:#c84b2f!important;}
</style>""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def gc(s):
    return "red" if s<=40 else ("amber" if s<=70 else "green")

def grade_label(s):
    return "Poor" if s<=40 else ("Average" if s<=70 else "Strong")

STATUS_C  = {"fail":"#c84b2f","warn":"#c8962f","pass":"#2a8a5e"}
STATUS_BG = {"fail":"#fde8e5","warn":"#fdf3e0","pass":"#e4f5ec"}
STATUS_IC = {"fail":"❌","warn":"⚠️","pass":"✅"}
CHIP_CLS  = {"fail":"chip-f","warn":"chip-w","pass":"chip-p"}

def validate(url, email):
    e = {}
    if not url.strip(): e["url"] = "Please enter a website URL."
    else:
        test = url if url.startswith("http") else "https://"+url
        if not validators.url(test): e["url"] = "Please enter a valid URL."
    if not email.strip(): e["email"] = "Email is required."
    elif not validators.email(email): e["email"] = "Please enter a valid email address."
    return e

def render_banner(data, domain):
    s = data["overall_score"]; sc = data.get("seo_score",0); ai = data.get("ai_score",0)
    grade = data["overall_grade"]; color = gc(s)
    saved = f" · Saved {data['saved_at']}" if data.get("saved_at") else ""
    kw_tag = f" · Keyword: <em>{data.get('keyword','')}</em>" if data.get("keyword") else ""
    st.markdown(f"""
    <div class="score-banner">
      <div>
        <div class="score-eye">Total Score</div>
        <div class="score-big">{s}</div>
        <div class="score-eye">out of 100</div>
      </div>
      <div class="score-pair">
        <div class="score-pill-box">
          <div class="pill-num sg-{'r' if sc<=40 else 'a' if sc<=70 else 'g'}">{sc}</div>
          <div class="pill-label">SEO Score</div>
        </div>
        <div class="score-pill-box">
          <div class="pill-num sg-{'r' if ai<=40 else 'a' if ai<=70 else 'g'}">{ai}</div>
          <div class="pill-label">AI Score</div>
        </div>
      </div>
      <div class="score-right">
        <span class="score-eye">Overall Grade</span>
        <span class="sg-{color[0]}">{grade}</span>
        <span class="score-sub">{domain}{saved}</span>
        <span class="score-sub" style="color:rgba(255,255,255,.4)">{kw_tag}</span>
      </div>
    </div>""", unsafe_allow_html=True)

def render_check_cards(checks):
    for c in checks:
        st_c = STATUS_C.get(c["status"],"#888")
        st_bg = STATUS_BG.get(c["status"],"#f5f5f5")
        chip = CHIP_CLS.get(c["status"],"")
        fix_html = (f'<div class="fix-box"><div class="fix-lbl">🔧 How to fix</div>'
                    f'<div class="fix-txt">{c.get("how_to_fix","")}</div></div>'
                    if c["status"] in ("fail","warn") else "")
        details_html = ""
        if c.get("details"):
            d_items = "".join([f'<li style="margin-bottom:6px;">{d}</li>' for d in c["details"]])
            details_html = f'<div style="margin-top:10px; padding:10px; background:var(--cc-bg,#f9f9f9); border:1px solid rgba(13,13,13,0.05); border-radius:6px; font-size:0.82rem; max-height:220px; overflow-y:auto; color:#3a3530;"><strong style="font-family:\'Syne\',sans-serif;font-size:0.85rem;">Detailed Issues ({len(c["details"])}):</strong><ul style="margin-top:6px; padding-left:20px;">{d_items}</ul></div>'

        st.markdown(f"""
        <div class="chk-card" style="--cc:{st_c};--cc-bg:{st_bg};">
          <div class="chk-header">
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="chip {chip}">{c['status'].upper()}</span>
              <span class="chk-name">{c['name']}</span>
            </div>
            <span class="chk-badge">{c['score']}/{c['max_score']} pts</span>
          </div>
          <div class="found-box">🔍 <strong>What we found:</strong> {c['found']}</div>
          <div class="impact-box">💥 <strong>Impact:</strong> {c['impact']}</div>
          {fix_html}
          {details_html}
        </div>""", unsafe_allow_html=True)

def render_full_report(data):
    url = data.get("url",""); domain = urlparse(url).netloc.replace("www.","")
    seo_mod = data.get("seo_module",{}); ai_mod = data.get("ai_module",{})
    error = data.get("error")
    if error:
        st.error(f"**Audit error:** {error}"); return

    render_banner(data, domain)

    left, right = st.columns([3, 2])
    with left:
        st.markdown('<div class="sec-label">Key Insights</div>', unsafe_allow_html=True)
        for ins in data.get("insights",[]):
            st.markdown(f"""
            <div class="ins-card">
              <span style="font-size:14px;margin-top:2px;">{ins['icon']}</span>
              <div>
                <div class="ins-title">{ins['title']}</div>
                <div class="ins-found">{ins['found']}</div>
                <div class="ins-impact">{ins['impact']}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="sec-label">Audit Summary</div>', unsafe_allow_html=True)
        all_checks = (seo_mod.get("checks",[]) if seo_mod else []) + (ai_mod.get("checks",[]) if ai_mod else [])
        total = len(all_checks)
        fails = sum(1 for c in all_checks if c["status"]=="fail")
        warns = sum(1 for c in all_checks if c["status"]=="warn")
        passes = sum(1 for c in all_checks if c["status"]=="pass")
        for label, val, col in [
            ("Total checks run", total, "#0d0d0d"),
            ("❌ Failed", fails, "#c84b2f"),
            ("⚠️ Warnings", warns, "#c8962f"),
            ("✅ Passed", passes, "#2a8a5e"),
        ]:
            st.markdown(f"""
            <div class="stat-box">
              <span style="font-size:.83rem;color:#4a4540;">{label}</span>
              <span class="stat-val" style="color:{col};">{val}</span>
            </div>""", unsafe_allow_html=True)
        ft = data.get("fetch_time_ms", 0)
        st.markdown(f'<div style="text-align:center;font-size:11px;color:#9a9285;margin-top:8px;">Fetched in {ft}ms</div>', unsafe_allow_html=True)

    # SEO Checks
    st.markdown('<div class="sec-label">SEO Score — Detailed Report</div>', unsafe_allow_html=True)
    if seo_mod:
        seo_checks = seo_mod.get("checks", [])
        seo_fails  = sum(1 for c in seo_checks if c["status"]=="fail")
        seo_warns  = sum(1 for c in seo_checks if c["status"]=="warn")
        seo_passes = sum(1 for c in seo_checks if c["status"]=="pass")
        sorted_seo = sorted(seo_checks, key=lambda c:(0 if c["status"]=="fail" else 1 if c["status"]=="warn" else 2))
        with st.expander(f"📊 SEO Score: {seo_mod['score']}/100  ·  ❌ {seo_fails} failed  ·  ⚠️ {seo_warns} warnings  ·  ✅ {seo_passes} passed", expanded=True):
            # Filter tabs
            tab_all, tab_fail, tab_warn, tab_pass = st.tabs(["All", "Failed", "Warnings", "Passed"])
            with tab_all:   render_check_cards(sorted_seo)
            with tab_fail:  render_check_cards([c for c in sorted_seo if c["status"]=="fail"])
            with tab_warn:  render_check_cards([c for c in sorted_seo if c["status"]=="warn"])
            with tab_pass:  render_check_cards([c for c in sorted_seo if c["status"]=="pass"])

    # AI Checks
    st.markdown('<div class="sec-label">AI Score — Detailed Report</div>', unsafe_allow_html=True)
    if ai_mod:
        ai_checks = ai_mod.get("checks", [])
        ai_fails  = sum(1 for c in ai_checks if c["status"]=="fail")
        ai_warns  = sum(1 for c in ai_checks if c["status"]=="warn")
        ai_passes = sum(1 for c in ai_checks if c["status"]=="pass")
        sorted_ai = sorted(ai_checks, key=lambda c:(0 if c["status"]=="fail" else 1 if c["status"]=="warn" else 2))
        with st.expander(f"🤖 AI Score: {ai_mod['score']}/100  ·  ❌ {ai_fails} failed  ·  ⚠️ {ai_warns} warnings  ·  ✅ {ai_passes} passed", expanded=True):
            tab_all, tab_fail, tab_warn, tab_pass = st.tabs(["All", "Failed", "Warnings", "Passed"])
            with tab_all:   render_check_cards(sorted_ai)
            with tab_fail:  render_check_cards([c for c in sorted_ai if c["status"]=="fail"])
            with tab_warn:  render_check_cards([c for c in sorted_ai if c["status"]=="warn"])
            with tab_pass:  render_check_cards([c for c in sorted_ai if c["status"]=="pass"])

    # CTA
    st.markdown("""
    <div class="cta-block">
      <div class="cta-eye">Want expert help?</div>
      <div class="cta-h">Get your complete AI SEO report</div>
      <div class="cta-s">This free audit shows the issues. Our full service includes keyword gap analysis, competitor benchmarking, content rewrites, and a 30-day implementation plan.</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("")
    c1, c2, c3 = st.columns(3)
    with c1: st.button("📋  Get Full AI SEO Report", type="primary", use_container_width=True, key=f"cta1_{url[:15]}")
    with c2: st.button("📩  Request Detailed Audit", type="secondary", use_container_width=True, key=f"cta2_{url[:15]}")
    with c3:
        st.download_button("⬇️  Download Report JSON",
            data=json.dumps(data, indent=2, ensure_ascii=False),
            file_name=f"seo_audit_{domain}.json", mime="application/json",
            use_container_width=True, key=f"dl_{url[:15]}")

# ── Session state ─────────────────────────────────────────────────────────────
for k,v in [("report",None),("show_results",False),("view_saved",None)]:
    if k not in st.session_state: st.session_state[k] = v

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗄️ Audit History")
    stats = get_stats()
    if stats:
        c1,c2 = st.columns(2)
        c1.metric("Audits",  stats.get("total_audits",0))
        c2.metric("Leads",   stats.get("unique_leads",0))
        c1.metric("Domains", stats.get("unique_domains",0))
        c2.metric("Avg",     stats.get("avg_overall","—"))
    st.divider()
    rows = get_recent_audits(limit=60)
    if rows:
        for r in rows:
            s = r.get("overall_score") or 0
            em = "🟢" if s>70 else ("🟡" if s>40 else "🔴")
            label = f"{em} {r['domain'] or r['url'][:28]}  ·  {s}"
            tip = f"{r['created_at'][:16]}  ·  {r['email']}  ·  kw: {r.get('keyword','—')}"
            if st.button(label, key=f"v_{r['id']}", help=tip, use_container_width=True):
                st.session_state.view_saved = r["id"]
                st.session_state.show_results = False
                st.session_state.report = None
                st.rerun()
        st.divider()
        csv_data = export_csv()
        if csv_data:
            st.download_button("⬇️ Export CSV", data=csv_data,
                file_name="seo_audit_leads.csv", mime="text/csv", use_container_width=True)
    else:
        st.info("No audits yet.")
    if st.session_state.view_saved or st.session_state.show_results:
        st.divider()
        if st.button("← New audit", use_container_width=True):
            st.session_state.show_results=False; st.session_state.report=None; st.session_state.view_saved=None; st.rerun()

# ── SAVED AUDIT VIEW ──────────────────────────────────────────────────────────
if st.session_state.view_saved:
    data = get_audit_by_id(st.session_state.view_saved)
    if data:
        d = urlparse(data.get("url","")).netloc.replace("www.","")
        st.markdown(f'<div class="hero-badge">Saved Audit — {d}</div>', unsafe_allow_html=True)
        render_full_report(data)
    else:
        st.error("Could not load this audit.")
    st.stop()

# ── HERO + FORM ───────────────────────────────────────────────────────────────
if not st.session_state.show_results:
    st.markdown('<div class="hero-badge">Free AI SEO Audit</div>', unsafe_allow_html=True)
    st.markdown("""
    <h1 class="hero-title">How visible are you to <em>AI search?</em></h1>
    <p class="hero-sub">Enter your URL and target keyword for a full audit — SEO score + AI visibility score with detailed fix instructions for every issue.</p>
    """, unsafe_allow_html=True)
    st.markdown("---")

    col_u, col_e = st.columns(2)
    with col_u: url_input = st.text_input("Website URL", placeholder="https://yourwebsite.com")
    with col_e: email_input = st.text_input("Your Email *(required)*", placeholder="you@company.com")
    kw_input = st.text_input("Target Keyword *(recommended — e.g. 'best python seo tools')*",
                              placeholder="Enter your primary target keyword for deeper analysis")

    c1, c2 = st.columns([3,1])
    with c1: run_btn = st.button("🔍  Run AI SEO Audit", type="primary", use_container_width=True)
    with c2: st.markdown('<p style="font-size:11px;color:#9a9285;padding-top:10px;">No spam ever.</p>', unsafe_allow_html=True)

    if run_btn:
        errs = validate(url_input, email_input)
        if errs:
            for _,m in errs.items(): st.error(m)
        else:
            norm_url = url_input if url_input.startswith("http") else "https://"+url_input
            prog = st.progress(0); txt = st.empty()
            steps = [(12,"Fetching page content…"),(28,"Parsing HTML structure…"),
                     (48,"Analysing SEO signals…"),(65,"Evaluating keyword usage…"),
                     (80,"Checking AI visibility…"),(92,"Calculating scores…")]
            for pct, msg in steps:
                txt.markdown(f"**{msg}**"); prog.progress(pct); time.sleep(0.3)
            report = run_audit(norm_url, email_input, kw_input.strip())
            save_audit(report)
            prog.progress(100); txt.markdown("**Done! Loading your report…**")
            time.sleep(0.3); prog.empty(); txt.empty()
            st.session_state.report = report
            st.session_state.show_results = True
            st.rerun()

# ── LIVE RESULTS ──────────────────────────────────────────────────────────────
if st.session_state.show_results and st.session_state.report:
    report = st.session_state.report
    domain = urlparse(report.url).netloc.replace("www.","")
    if report.error:
        st.error(f"**Could not audit:** {report.error}")
        if st.button("← Try again"): st.session_state.show_results=False; st.session_state.report=None; st.rerun()
        st.stop()
    st.markdown(f'<div class="hero-badge">Audit Complete — {domain}</div>', unsafe_allow_html=True)
    render_full_report(_report_to_dict(report))
    st.markdown(f'<div style="text-align:center;margin-top:1.5rem;font-size:11px;color:#9a9285;">Audited <strong>{domain}</strong> · Scoring is heuristic-based · Results for guidance only</div>', unsafe_allow_html=True)