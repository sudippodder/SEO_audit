"""
external_authority_checks.py
Section: External Authority — checks based on real external profile validation.
Uses ExternalValidationResult from external_validator.py.
"""
from typing import Optional
from .geo_checks import CheckResult
from .external_validator import ExternalValidationResult, ExternalProfile, get_profile_by_platform


def _profile_status_msg(profile: Optional[ExternalProfile], platform: str) -> str:
    """Generate context-aware status message for a platform."""
    if profile is None:
        return f"{platform} was not checked."
    if profile.verification_status == "error":
        return f"Could not verify {platform} profile ({profile.error_message or 'connection error'})."
    if not profile.exists:
        return f"No {platform} profile detected for this brand."
    # Profile exists
    parts = [f"✅ {platform} profile detected"]
    if profile.url:
        parts.append(f"at {profile.url}")
    if profile.rating is not None:
        parts.append(f"— rated {profile.rating}/5")
    if profile.review_count is not None:
        parts.append(f"({profile.review_count} reviews)")
    return " ".join(parts) + "."


# ═══════════════════════════════════════════════════════════════════════════
# EXTERNAL AUTHORITY CHECKS
# ═══════════════════════════════════════════════════════════════════════════

def check_trustpilot_presence(ext: ExternalValidationResult) -> CheckResult:
    """Trustpilot profile validation — verified externally."""
    profile = get_profile_by_platform(ext, "Trustpilot")
    if profile and profile.exists:
        rating_info = ""
        if profile.rating is not None:
            rating_info = f" Rating: {profile.rating}/5."
        if profile.review_count is not None:
            rating_info += f" Reviews: {profile.review_count}."
            if profile.review_count < 20:
                return CheckResult(
                    "Trustpilot profile", 3, 4, "warn",
                    f"✅ Trustpilot profile detected.{rating_info} Review count is low — aim for 50+ reviews.",
                    "Trustpilot is a top third-party trust signal for AI citation systems.",
                    "Actively request reviews from satisfied clients. Respond to existing reviews to boost engagement.",
                    effort="medium")
        return CheckResult(
            "Trustpilot profile", 4, 4, "pass",
            f"✅ Trustpilot profile verified and active.{rating_info}",
            "Active Trustpilot profiles significantly boost third-party trust signals for AI citation.",
            "No action needed. Continue collecting reviews and responding to feedback.",
            effort="quick")
    if profile and profile.verification_status == "error":
        return CheckResult(
            "Trustpilot profile", 1, 4, "warn",
            f"🔍 Trustpilot profile could not be verified ({profile.error_message or 'platform did not respond'}).",
            "Trustpilot is a major trust signal — please verify your listing manually.",
            "Check https://www.trustpilot.com for your business listing. Create one if it doesn't exist.",
            effort="quick")
    return CheckResult(
        "Trustpilot profile", 0, 4, "fail",
        "❌ No Trustpilot profile detected for this brand.",
        "Missing Trustpilot profile is a significant gap — AI systems use review platforms to assess brand credibility.",
        "Create a Trustpilot business profile at business.trustpilot.com. Invite clients to leave reviews.",
        effort="medium")


def check_clutch_g2_presence(ext: ExternalValidationResult) -> CheckResult:
    """Clutch and G2 presence — verified externally."""
    clutch = get_profile_by_platform(ext, "Clutch")
    g2 = get_profile_by_platform(ext, "G2")

    clutch_found = clutch and clutch.exists
    g2_found = g2 and g2.exists
    found_platforms = []
    details = []

    if clutch_found:
        found_platforms.append("Clutch")
        r = f" ({clutch.rating}/5)" if clutch.rating else ""
        details.append(f"✅ Clutch profile verified{r}")
    if g2_found:
        found_platforms.append("G2")
        r = f" ({g2.rating}/5)" if g2.rating else ""
        details.append(f"✅ G2 profile verified{r}")

    if len(found_platforms) == 2:
        return CheckResult(
            "Clutch / G2 profiles", 4, 4, "pass",
            f"Both Clutch and G2 profiles verified. {'; '.join(details)}.",
            "Dual review platform presence is a strong B2B trust signal for AI citation systems.",
            "No action needed. Actively collect reviews on both platforms.",
            effort="quick")
    if len(found_platforms) == 1:
        missing = "G2" if "Clutch" in found_platforms else "Clutch"
        return CheckResult(
            "Clutch / G2 profiles", 3, 4, "warn",
            f"{details[0]}. ⚠️ {missing} profile not detected.",
            "Single review platform is good but multi-platform presence strengthens AI trust signals.",
            f"Create a {missing} profile to complement your {found_platforms[0]} presence.",
            effort="medium")
    return CheckResult(
        "Clutch / G2 profiles", 0, 4, "fail",
        "❌ No Clutch or G2 profiles detected for this brand.",
        "B2B review platforms are critical for AI-assessed brand credibility, especially for service companies.",
        "Create profiles on both Clutch (clutch.co) and G2 (g2.com). Invite clients to leave detailed reviews.",
        effort="medium")


def check_linkedin_company(ext: ExternalValidationResult) -> CheckResult:
    """LinkedIn company page — verified externally."""
    profile = get_profile_by_platform(ext, "LinkedIn")
    if profile and profile.exists:
        return CheckResult(
            "LinkedIn company page", 3, 3, "pass",
            f"✅ LinkedIn company page verified: {profile.url}",
            "LinkedIn company pages are a primary entity signal for AI knowledge graph construction.",
            "No action needed. Keep the profile updated with company info, team, and recent posts.",
            effort="quick")
    if profile and profile.verification_status == "error":
        return CheckResult(
            "LinkedIn company page", 1, 3, "warn",
            "🔍 LinkedIn company page could not be verified (requires login to confirm).",
            "LinkedIn is a key entity signal — verify your company page exists and is complete.",
            "Ensure your LinkedIn company page is complete with description, logo, website URL, and team members.",
            effort="quick")
    return CheckResult(
        "LinkedIn company page", 0, 3, "fail",
        "❌ No LinkedIn company page detected for this brand.",
        "Missing LinkedIn presence significantly weakens entity signals in AI knowledge graphs.",
        "Create a LinkedIn company page with: logo, description, website, industry, size, location. Link from your site.",
        effort="quick")


def check_youtube_presence(ext: ExternalValidationResult) -> CheckResult:
    """YouTube channel — verified externally."""
    profile = get_profile_by_platform(ext, "YouTube")
    if profile and profile.exists:
        return CheckResult(
            "YouTube channel", 2, 2, "pass",
            f"✅ YouTube channel detected: {profile.url}",
            "YouTube presence strengthens multi-platform entity signals and provides additional citation surfaces.",
            "No action needed. Ensure channel description links back to your website.",
            effort="quick")
    return CheckResult(
        "YouTube channel", 0, 2, "warn",
        "⚠️ No YouTube channel detected for this brand.",
        "YouTube is the second-largest search engine — a channel expands your entity footprint for AI.",
        "Consider creating a YouTube channel with educational/expert content related to your services.",
        effort="complex")


def check_crunchbase_presence(ext: ExternalValidationResult) -> CheckResult:
    """Crunchbase profile — verified externally."""
    profile = get_profile_by_platform(ext, "Crunchbase")
    if profile and profile.exists:
        return CheckResult(
            "Crunchbase profile", 2, 2, "pass",
            f"✅ Crunchbase profile detected: {profile.url}",
            "Crunchbase profiles strengthen entity recognition — AI systems use it as a structured data source.",
            "No action needed. Keep the profile updated with company details, funding, and team info.",
            effort="quick")
    if profile and profile.verification_status == "error":
        return CheckResult(
            "Crunchbase profile", 1, 2, "warn",
            "🔍 Crunchbase profile could not be verified.",
            "Crunchbase strengthens entity signals — verify your listing manually.",
            "Check crunchbase.com for your company. Create or claim a profile if it doesn't exist.",
            effort="medium")
    return CheckResult(
        "Crunchbase profile", 0, 2, "warn",
        "⚠️ No Crunchbase profile detected.",
        "Crunchbase profiles help AI systems build structured company entity data.",
        "Create a Crunchbase profile with: founding date, location, industry, team size, and website.",
        effort="medium")


def check_wikipedia_wikidata(ext: ExternalValidationResult) -> CheckResult:
    """Wikipedia and Wikidata presence — verified externally."""
    wiki = get_profile_by_platform(ext, "Wikipedia")
    wikidata = get_profile_by_platform(ext, "Wikidata")

    wiki_found = wiki and wiki.exists
    wikidata_found = wikidata and wikidata.exists

    if wiki_found and wikidata_found:
        desc = wiki.extra_data.get("description", "")
        return CheckResult(
            "Wikipedia / Wikidata presence", 4, 4, "pass",
            f"✅ Wikipedia article found. ✅ Wikidata entity found (QID: {wikidata.extra_data.get('qid', 'N/A')}). {f'Description: {desc}' if desc else ''}",
            "Wikipedia + Wikidata presence is the strongest possible entity signal for AI Knowledge Panel eligibility.",
            "No action needed. This is the gold standard for entity recognition.",
            effort="complex")
    if wiki_found:
        return CheckResult(
            "Wikipedia / Wikidata presence", 3, 4, "warn",
            f"✅ Wikipedia article found. ⚠️ Wikidata entity not confirmed.",
            "Wikipedia article is excellent — adding a matching Wikidata entry completes the entity loop.",
            "Create a Wikidata item for your organization linking to the Wikipedia article.",
            effort="complex")
    if wikidata_found:
        desc = wikidata.extra_data.get("description", "")
        return CheckResult(
            "Wikipedia / Wikidata presence", 2, 4, "warn",
            f"⚠️ No Wikipedia article. ✅ Wikidata entity found ({desc}).",
            "Wikidata presence is good but a Wikipedia article would significantly boost Knowledge Panel eligibility.",
            "Consider working toward Wikipedia notability criteria. Maintain and expand the Wikidata entry.",
            effort="complex")
    return CheckResult(
        "Wikipedia / Wikidata presence", 0, 4, "fail",
        "❌ No Wikipedia article or Wikidata entity found for this brand.",
        "Absence from Wikipedia/Wikidata significantly limits Knowledge Panel eligibility and AI entity recognition.",
        "Long-term: build notability through press coverage, awards, and third-party citations. Short-term: create a Wikidata entry.",
        effort="complex")


def check_knowledge_panel_signals(ext: ExternalValidationResult) -> CheckResult:
    """Knowledge Panel eligibility — combined signal check."""
    wiki = get_profile_by_platform(ext, "Wikipedia")
    wikidata = get_profile_by_platform(ext, "Wikidata")
    linkedin = get_profile_by_platform(ext, "LinkedIn")
    crunchbase = get_profile_by_platform(ext, "Crunchbase")

    signals = {
        "Wikipedia article": wiki and wiki.exists,
        "Wikidata entity": wikidata and wikidata.exists,
        "LinkedIn company": linkedin and linkedin.exists,
        "Crunchbase profile": crunchbase and crunchbase.exists,
    }
    found = [k for k, v in signals.items() if v]
    missing = [k for k, v in signals.items() if not v]

    if len(found) >= 3:
        return CheckResult(
            "Knowledge Panel eligibility (external)", 3, 3, "pass",
            f"Strong Knowledge Panel signals: {', '.join(found)}.",
            "Multiple confirmed external entity sources maximize Knowledge Panel eligibility.",
            "No action needed. Ensure all profiles are consistent and link back to your website.",
            effort="complex")
    if len(found) >= 1:
        return CheckResult(
            "Knowledge Panel eligibility (external)", 2, 3, "warn",
            f"Some entity signals confirmed: {', '.join(found)}. Missing: {', '.join(missing)}.",
            "Additional external entity sources would strengthen Knowledge Panel eligibility.",
            f"Priority: create/claim {', '.join(missing[:2])} profiles.",
            effort="complex")
    return CheckResult(
        "Knowledge Panel eligibility (external)", 0, 3, "fail",
        f"No external entity sources confirmed. Missing: {', '.join(missing)}.",
        "Without external entity confirmation, Knowledge Panel eligibility is very low.",
        "Start with LinkedIn company page and Crunchbase profile. Work toward Wikipedia notability.",
        effort="complex")


def check_brand_directory_presence(ext: ExternalValidationResult) -> CheckResult:
    """Overall brand presence across directories and platforms."""
    total_checked = len([p for p in ext.profiles if p.verification_status in ("checked", "heuristic")])
    found = ext.profiles_found
    ratio = found / max(total_checked, 1)

    if ratio >= 0.7 and found >= 5:
        return CheckResult(
            "Brand directory presence", 3, 3, "pass",
            f"Strong brand presence: {found}/{total_checked} platforms confirmed. "
            f"Found on: {', '.join(p.platform for p in ext.profiles if p.exists)}.",
            "Wide directory presence significantly strengthens brand entity signals across AI knowledge systems.",
            "No action needed. Monitor and maintain all profiles.",
            effort="medium")
    if found >= 3:
        missing_str = ", ".join(ext.profiles_missing[:4]) if ext.profiles_missing else "none"
        return CheckResult(
            "Brand directory presence", 2, 3, "warn",
            f"Moderate brand presence: {found}/{total_checked} platforms. Missing: {missing_str}.",
            "Expanding directory presence would strengthen AI entity recognition.",
            f"Create profiles on: {missing_str}.",
            effort="medium")
    missing_str = ", ".join(ext.profiles_missing[:4]) if ext.profiles_missing else "none"
    return CheckResult(
        "Brand directory presence", 0, 3, "fail",
        f"Weak brand presence: only {found}/{total_checked} platforms confirmed. Missing: {missing_str}.",
        "Limited directory presence significantly weakens AI entity recognition and citation probability.",
        f"Priority: create profiles on {missing_str}. Start with LinkedIn, Trustpilot, and Clutch/G2.",
        effort="medium")


def check_google_business(ext: ExternalValidationResult) -> CheckResult:
    """Google Business Profile — heuristic check."""
    profile = get_profile_by_platform(ext, "Google Business")
    # GBP cannot be verified without Google API, so this is always a recommendation
    if profile and profile.exists:
        return CheckResult(
            "Google Business Profile", 3, 3, "pass",
            "✅ Google Business Profile signals detected.",
            "Google Business Profile is critical for local AI visibility and Knowledge Panel generation.",
            "No action needed. Keep the profile updated with hours, photos, and responses to reviews.",
            effort="quick")
    return CheckResult(
        "Google Business Profile", 1, 3, "warn",
        "⚠️ Google Business Profile could not be automatically verified (requires manual check or API).",
        "Google Business Profile is critical for local search and AI Knowledge Panel generation.",
        "Verify your Google Business Profile at business.google.com. Ensure NAP data matches your website.",
        effort="quick")
