import re


ANALYSIS_SYSTEM_PROMPT = """You are a business analyst.

Analyze the business deeply.

Generate:
1. 3 problems (different types)
2. 3 insights (UX, revenue, reviews, competitors)
3. Confidence score (HIGH/MEDIUM/LOW)

Rules:
- No generic insights
- No repetition
- Must be based on real data
- Reject if insights are similar
- Return JSON only.
"""


POSITIVE_REVIEW_MARKERS = {
    "fast",
    "friendly",
    "helpful",
    "professional",
    "responsive",
    "quick",
    "great",
    "excellent",
    "honest",
    "reliable",
}

NEGATIVE_REVIEW_MARKERS = {
    "slow",
    "late",
    "expensive",
    "rude",
    "poor",
    "issue",
    "problem",
    "delay",
    "confusing",
    "unresponsive",
}

REVIEW_STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "because",
    "business",
    "from",
    "have",
    "just",
    "local",
    "really",
    "service",
    "that",
    "their",
    "them",
    "they",
    "this",
    "very",
    "were",
    "with",
    "would",
    "your",
}


def _clean_reviews(reviews):
    cleaned = []
    for review in reviews or []:
        text = str(review or "").strip()
        if text:
            cleaned.append(text)
    return cleaned


def _top_review_keywords(reviews, limit=4):
    counts = {}
    for review in reviews:
        for token in re.findall(r"[a-z0-9][a-z0-9/&+-]{3,}", review.lower()):
            if token in REVIEW_STOPWORDS:
                continue
            counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _count in ranked[:limit]]


def build_review_intelligence(reviews):
    cleaned_reviews = _clean_reviews(reviews)
    if not cleaned_reviews:
        return {
            "positive": "No review positives were captured.",
            "negative": "No review complaints were captured.",
            "patterns": "No review patterns were captured.",
        }

    joined = " ".join(cleaned_reviews).lower()
    positive_hits = sorted(word for word in POSITIVE_REVIEW_MARKERS if word in joined)
    negative_hits = sorted(word for word in NEGATIVE_REVIEW_MARKERS if word in joined)
    keywords = _top_review_keywords(cleaned_reviews)

    positive = (
        "Positive review language highlights: " + ", ".join(positive_hits[:4])
        if positive_hits
        else "Reviews suggest the business already has usable trust proof."
    )
    negative = (
        "Negative review language highlights: " + ", ".join(negative_hits[:4])
        if negative_hits
        else "No repeated complaints were obvious in the sampled reviews."
    )
    patterns = (
        "Repeated review patterns: " + ", ".join(keywords)
        if keywords
        else "Review patterns were too thin to summarize."
    )

    return {
        "positive": positive,
        "negative": negative,
        "patterns": patterns,
    }


def build_analysis_prompt(data, persona_name, persona_desc):
    review_intelligence = data.get("review_intelligence") or {}
    return f"""BUSINESS:
Name: {data['name']}
Category: {data['category']}
Location: {data['location']}
Rating: {data['rating']}
Review Count: {data['reviews']}
Persona Lens: {persona_name} -> {persona_desc}

WEBSITE DATA:
{data['website_text']}

REVIEW INTELLIGENCE:
Positive: {review_intelligence.get('positive', 'No review positives were captured.')}
Negative: {review_intelligence.get('negative', 'No review complaints were captured.')}
Patterns: {review_intelligence.get('patterns', 'No review patterns were captured.')}

REVIEW SNIPPETS:
{data['reviews_text']}

COMPETITOR INTELLIGENCE:
{data['competitors_text']}

SOURCE EVIDENCE:
{data['evidence_text']}

ANALYSIS TASK:
1. Generate exactly 3 problems. They should be different types where possible.
2. Generate exactly 3 insights. Spread them across UX, revenue/trust, reviews, and competitor angle where the evidence allows it.
3. Set confidence to HIGH, MEDIUM, or LOW.

RULES:
- Every problem and insight must be tied to the supplied evidence.
- Do not repeat the same idea with new wording.
- Do not give generic website advice.
- Confidence should be HIGH only when the evidence is direct and specific.

OUTPUT JSON:
{{
  "problems": ["...", "...", "..."],
  "insights": ["...", "...", "..."],
  "confidence": "HIGH"
}}
"""
