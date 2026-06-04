"""
ai_tester.py
Live AI visibility testing — queries OpenAI (ChatGPT) with brand/keyword
prompts and analyses whether the brand is mentioned, recommended, or cited.

Requires: OPENAI_API_KEY in environment or passed directly.
"""
import os
import re
import time
import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class AITestQuery:
    """A single test query sent to the AI model."""
    query_type: str        # "brand_knowledge" | "keyword_recommendation" | "competitor_comparison"
    prompt: str            # The actual prompt sent
    response: str = ""     # Raw response from AI
    brand_mentioned: bool = False
    mention_count: int = 0
    sentiment: str = ""    # "positive" | "neutral" | "negative" | "not_mentioned"
    position: str = ""     # "first" | "top3" | "mentioned" | "not_mentioned"
    key_facts_accurate: List[str] = field(default_factory=list)
    key_facts_inaccurate: List[str] = field(default_factory=list)
    competitor_mentions: List[str] = field(default_factory=list)
    error: str = ""
    latency_ms: int = 0


@dataclass
class AITestResult:
    """Aggregated result from all AI test queries."""
    queries: List[AITestQuery] = field(default_factory=list)
    brand_recognized: bool = False
    brand_recommended: bool = False
    overall_sentiment: str = ""  # "positive" | "neutral" | "negative" | "unknown"
    visibility_score: int = 0   # 0-100
    total_mentions: int = 0
    competitors_found: List[str] = field(default_factory=list)
    model_used: str = ""
    total_latency_ms: int = 0
    api_error: str = ""
    tested: bool = False


def _get_openai_client(api_key: str = ""):
    """Get OpenAI client, returns (client, error_msg)."""
    key = api_key or os.environ.get("OPENAI_API_KEY", "")
    if not key:
        return None, "No OpenAI API key provided"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        return client, ""
    except ImportError:
        return None, "openai package not installed (pip install openai)"
    except Exception as e:
        return None, f"OpenAI client error: {str(e)[:100]}"


def _query_openai(client, prompt: str, model: str = "gpt-4o-mini") -> tuple:
    """
    Send a prompt to OpenAI and return (response_text, latency_ms, error).
    Uses gpt-4o-mini by default for cost efficiency.
    """
    start = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Answer the user's question factually and comprehensively. If you don't know something, say so."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.3,
        )
        text = resp.choices[0].message.content or ""
        latency = int((time.time() - start) * 1000)
        return text, latency, ""
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return "", latency, str(e)[:200]


def _analyze_response(response: str, brand_name: str, domain: str) -> dict:
    """
    Analyze an AI response for brand mentions, sentiment, and positioning.
    Returns dict with analysis results.
    """
    if not response:
        return {
            "brand_mentioned": False, "mention_count": 0,
            "sentiment": "not_mentioned", "position": "not_mentioned",
            "competitors": [],
        }

    resp_lower = response.lower()
    brand_lower = brand_name.lower()
    domain_lower = domain.lower().replace("www.", "")

    # Brand mention detection — check brand name and domain
    brand_variants = [
        brand_lower,
        brand_lower.replace(" ", ""),
        brand_lower.replace("-", ""),
        domain_lower.split(".")[0],
    ]
    brand_variants = list(set(v for v in brand_variants if len(v) >= 3))

    mention_count = 0
    brand_mentioned = False
    for variant in brand_variants:
        count = resp_lower.count(variant)
        if count > 0:
            brand_mentioned = True
            mention_count += count

    # Position detection — where does brand appear in numbered lists?
    position = "not_mentioned"
    if brand_mentioned:
        # Check if brand appears in a numbered list
        lines = response.split("\n")
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(v in line_lower for v in brand_variants):
                # Check for numbered position
                num_match = re.match(r'\s*(\d+)[\.\)\-]', line)
                if num_match:
                    pos = int(num_match.group(1))
                    if pos == 1:
                        position = "first"
                    elif pos <= 3:
                        position = "top3"
                    else:
                        position = "mentioned"
                    break
                elif i <= 3:
                    position = "top3"
                else:
                    position = "mentioned"
                break

    # Sentiment analysis — check context around brand mentions
    sentiment = "not_mentioned"
    if brand_mentioned:
        positive_signals = [
            "excellent", "outstanding", "highly recommended", "top choice",
            "leading", "best", "premier", "trusted", "reliable",
            "innovative", "strong reputation", "well-known", "popular",
            "recommended", "great choice", "solid", "reputable",
        ]
        negative_signals = [
            "controversy", "issues", "problems", "complaints", "poor",
            "avoid", "concerns", "negative", "criticized", "weak",
        ]
        # Extract sentences containing brand
        sentences_with_brand = []
        for sent in re.split(r'[.!?]', resp_lower):
            if any(v in sent for v in brand_variants):
                sentences_with_brand.append(sent)

        context = " ".join(sentences_with_brand)
        pos_count = sum(1 for s in positive_signals if s in context)
        neg_count = sum(1 for s in negative_signals if s in context)

        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

    # Competitor detection — find other company names mentioned
    competitors = []
    # Common patterns: "1. CompanyName", "**CompanyName**", "- CompanyName"
    list_pattern = re.findall(r'\d+[\.\)]\s*\*?\*?([A-Z][A-Za-z0-9\s&\-\.]+)\*?\*?', response)
    bold_pattern = re.findall(r'\*\*([A-Z][A-Za-z0-9\s&\-\.]+)\*\*', response)
    all_names = list_pattern + bold_pattern
    for name in all_names:
        name_clean = name.strip().rstrip(".-,;:")
        if len(name_clean) >= 3 and name_clean.lower() not in [v for v in brand_variants]:
            if name_clean not in competitors and len(competitors) < 10:
                competitors.append(name_clean)

    return {
        "brand_mentioned": brand_mentioned,
        "mention_count": mention_count,
        "sentiment": sentiment,
        "position": position,
        "competitors": competitors,
    }


def run_ai_visibility_test(
    brand_name: str,
    domain: str,
    keyword: str = "",
    api_key: str = "",
    model: str = "gpt-4o-mini",
) -> AITestResult:
    """
    Run AI visibility tests against OpenAI.

    Sends 3 types of queries:
    1. Brand knowledge: "What do you know about [brand]?"
    2. Keyword recommendation: "What are the best [keyword] companies/tools?"
    3. Competitor comparison: "Compare [brand] with its competitors in [industry]"

    Args:
        brand_name: Company/brand name (e.g., "ValueCoders")
        domain: Website domain (e.g., "valuecoders.com")
        keyword: Target keyword (e.g., "software development company India")
        api_key: OpenAI API key
        model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)

    Returns:
        AITestResult with all test results
    """
    result = AITestResult(model_used=model)

    # Get client
    client, error = _get_openai_client(api_key)
    if client is None:
        result.api_error = error
        return result

    result.tested = True
    total_start = time.time()

    # ── Query 1: Brand Knowledge ──────────────────────────────────────────
    q1_prompt = (
        f"What do you know about {brand_name}? "
        f"Their website is {domain}. "
        f"Provide details about what they do, their services, reputation, and any notable facts."
    )
    q1 = AITestQuery(query_type="brand_knowledge", prompt=q1_prompt)
    text, latency, err = _query_openai(client, q1_prompt, model)
    q1.response = text
    q1.latency_ms = latency
    q1.error = err
    if not err:
        analysis = _analyze_response(text, brand_name, domain)
        q1.brand_mentioned = analysis["brand_mentioned"]
        q1.mention_count = analysis["mention_count"]
        q1.sentiment = analysis["sentiment"]
        q1.position = analysis["position"]
        q1.competitor_mentions = analysis["competitors"]
    result.queries.append(q1)

    # ── Query 2: Keyword Recommendation ───────────────────────────────────
    if keyword:
        q2_prompt = (
            f"What are the best {keyword}? "
            f"List the top companies or tools with brief descriptions. "
            f"Rank them by quality and reputation."
        )
    else:
        # Use domain-derived industry guess
        industry = brand_name.lower()
        q2_prompt = (
            f"What are the top companies similar to {brand_name} ({domain})? "
            f"List the leading alternatives and competitors."
        )
    q2 = AITestQuery(query_type="keyword_recommendation", prompt=q2_prompt)
    text, latency, err = _query_openai(client, q2_prompt, model)
    q2.response = text
    q2.latency_ms = latency
    q2.error = err
    if not err:
        analysis = _analyze_response(text, brand_name, domain)
        q2.brand_mentioned = analysis["brand_mentioned"]
        q2.mention_count = analysis["mention_count"]
        q2.sentiment = analysis["sentiment"]
        q2.position = analysis["position"]
        q2.competitor_mentions = analysis["competitors"]
    result.queries.append(q2)

    # ── Query 3: Competitor Comparison ────────────────────────────────────
    q3_prompt = (
        f"Compare {brand_name} ({domain}) with its main competitors. "
        f"What are their strengths and weaknesses? "
        f"Who would you recommend and why?"
    )
    q3 = AITestQuery(query_type="competitor_comparison", prompt=q3_prompt)
    text, latency, err = _query_openai(client, q3_prompt, model)
    q3.response = text
    q3.latency_ms = latency
    q3.error = err
    if not err:
        analysis = _analyze_response(text, brand_name, domain)
        q3.brand_mentioned = analysis["brand_mentioned"]
        q3.mention_count = analysis["mention_count"]
        q3.sentiment = analysis["sentiment"]
        q3.position = analysis["position"]
        q3.competitor_mentions = analysis["competitors"]
    result.queries.append(q3)

    # ── Aggregate Results ─────────────────────────────────────────────────
    result.total_latency_ms = int((time.time() - total_start) * 1000)
    result.brand_recognized = any(q.brand_mentioned for q in result.queries if not q.error)
    result.brand_recommended = any(
        q.position in ("first", "top3") for q in result.queries if not q.error
    )
    result.total_mentions = sum(q.mention_count for q in result.queries)

    # Aggregate competitors
    all_competitors = []
    for q in result.queries:
        for c in q.competitor_mentions:
            if c not in all_competitors:
                all_competitors.append(c)
    result.competitors_found = all_competitors[:15]

    # Overall sentiment
    sentiments = [q.sentiment for q in result.queries if q.sentiment and q.sentiment != "not_mentioned"]
    if sentiments:
        pos = sentiments.count("positive")
        neg = sentiments.count("negative")
        if pos > neg:
            result.overall_sentiment = "positive"
        elif neg > pos:
            result.overall_sentiment = "negative"
        else:
            result.overall_sentiment = "neutral"
    else:
        result.overall_sentiment = "unknown"

    # Visibility score (0-100)
    score = 0
    # Brand recognized by AI? (30 pts)
    if result.brand_recognized:
        score += 30
    # Brand recommended for keyword? (25 pts)
    q2_result = result.queries[1] if len(result.queries) > 1 else None
    if q2_result and q2_result.brand_mentioned:
        if q2_result.position == "first":
            score += 25
        elif q2_result.position == "top3":
            score += 20
        elif q2_result.position == "mentioned":
            score += 10
    # Positive sentiment? (20 pts)
    if result.overall_sentiment == "positive":
        score += 20
    elif result.overall_sentiment == "neutral":
        score += 10
    # Multiple mentions? (15 pts)
    if result.total_mentions >= 10:
        score += 15
    elif result.total_mentions >= 5:
        score += 10
    elif result.total_mentions >= 1:
        score += 5
    # Brand knowledge depth (10 pts) — based on response length for brand query
    q1_result = result.queries[0] if result.queries else None
    if q1_result and q1_result.brand_mentioned and len(q1_result.response) > 500:
        score += 10
    elif q1_result and q1_result.brand_mentioned and len(q1_result.response) > 200:
        score += 5

    result.visibility_score = min(score, 100)
    return result


def serialize_ai_test_result(result: AITestResult) -> dict:
    """Serialize AITestResult for JSON storage."""
    return {
        "tested": result.tested,
        "brand_recognized": result.brand_recognized,
        "brand_recommended": result.brand_recommended,
        "overall_sentiment": result.overall_sentiment,
        "visibility_score": result.visibility_score,
        "total_mentions": result.total_mentions,
        "competitors_found": result.competitors_found,
        "model_used": result.model_used,
        "total_latency_ms": result.total_latency_ms,
        "api_error": result.api_error,
        "queries": [
            {
                "query_type": q.query_type,
                "prompt": q.prompt,
                "response": q.response[:2000],  # Truncate for storage
                "brand_mentioned": q.brand_mentioned,
                "mention_count": q.mention_count,
                "sentiment": q.sentiment,
                "position": q.position,
                "competitor_mentions": q.competitor_mentions[:10],
                "error": q.error,
                "latency_ms": q.latency_ms,
            }
            for q in result.queries
        ],
    }
