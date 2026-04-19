import re
from collections import deque


BANNED_PHRASES = [
    "quick look",
    "not clear",
    "improve your online presence",
    "help businesses grow",
    "I hope this email finds you well",
    "I'm writing to you because",
    "I'd love to jump on a call",
    "Let me know if you're interested",
    "Best regards",
    "Sincerely",
    "To whom it may concern",
    "I am a web developer",
    "I can help you scale",
    "Boost your revenue",
    "Double your leads",
    "Cheap", "Discount", "Offer"
]


SOFT_CTA_MARKERS = [
    "if helpful, i can send",
    "if useful, i can send",
    "happy to send",
    "worth pointing out",
]


PERSONA_MARKERS = {
    "Revenue Hacker": ["revenue", "quote", "quotes", "jobs", "calls", "traffic"],
    "SEO Sniper": ["google", "maps", "review", "reviews", "search", "rank", "trust"],
    "CX Fixer": ["contact", "call", "booking", "book", "button", "form", "friction"],
    "Automation Operator": ["manual", "follow-up", "follow up", "admin", "back-and-forth", "time"],
    "Authority Builder": ["trust", "credibility", "brand", "proof", "premium", "specialist"],
    "Competitor Spy": ["competitor", "local market", "versus", "gap", "compared"],
}


GENERIC_MARKERS = [
    "digital presence",
    "grow your business",
    "better online presence",
    "more leads",
    "more conversions",
]


_RECENT_INSIGHTS = deque(maxlen=50)


def _tokens(text):
    return re.findall(r"[a-z0-9][a-z0-9/&+-]{3,}", (text or "").lower())


def _insight_used(insight, body):
    tokens = _tokens(insight)
    lower_body = (body or "").lower()
    return any(token in lower_body for token in tokens[:4])


def _has_soft_cta(body):
    lower_body = (body or "").lower()
    return any(marker in lower_body for marker in SOFT_CTA_MARKERS)


def _matches_hook(body, hook_type, competitor_names=None):
    hook_type = (hook_type or "").strip().lower()
    lower_body = (body or "").lower()
    paragraphs = [part.strip().lower() for part in (body or "").split("\n\n") if part.strip()]
    lead_window = "\n\n".join(paragraphs[:3])
    competitor_names = [str(name or "").strip().lower() for name in competitor_names or [] if str(name or "").strip()]

    if hook_type == "question":
        return "?" in lead_window
    if hook_type == "contrarian":
        return any(token in lower_body for token in ["probably is not", "usually is not", "is not awareness", "the issue is not"])
    if hook_type == "competitor":
        return any(name in lower_body for name in competitor_names) or "competitor" in lower_body or "compared" in lower_body or "comparison" in lower_body
    if hook_type == "observation":
        return True
    return False


def _matches_persona_logic(body, persona_name):
    markers = PERSONA_MARKERS.get(persona_name or "", [])
    lower_body = (body or "").lower()
    if not markers:
        return True
    return any(marker in lower_body for marker in markers)


def _dedupe(items):
    deduped = []
    seen = set()
    for item in items:
        cleaned = str(item or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        deduped.append(cleaned)
    return deduped


def remember_insight(insight):
    cleaned = str(insight or "").strip().lower()
    if cleaned:
        _RECENT_INSIGHTS.append(cleaned)


def is_repeated_insight(insight):
    cleaned = str(insight or "").strip().lower()
    return bool(cleaned and cleaned in _RECENT_INSIGHTS)


def _personalization_score(body):
    score = 0
    b = (body or "").lower()
    observables = [
        "phone number", "mobile view", "scroll", "call button", "contact form", "booking", "click", "visible", "tap-to-call", "above the fold",
        "slow", "loading", "speed", "fast", "broken", "link", "error", "404", "page", "dead end"
    ]
    if any(o in b for o in observables):
        score += 2
    industry_terms = ["emergency", "after-hours", "service page", "quote", "schedule", "leak", "hot water", "heating", "cooling", "door", "spring"]
    if any(i in b for i in industry_terms):
        score += 1
    return score


def quality_issues(
    email,
    subject="",
    analysis=None,
    persona_name=None,
    business_name=None,
    hook_type=None,
    selected_insight=None,
    competitor_names=None,
    confidence=None,
):
    analysis = analysis or {}
    issues = []
    body = (email or "").strip()
    lower_body = body.lower()
    lower_subject = (subject or "").lower()

    if not body:
        return ["email is empty"]

    if _personalization_score(body) < 2:
        issues.append("low personalization score (no observable site details)")

    word_count = len(body.split())
    if word_count < 100:
        issues.append(f"email is under the PDF minimum ({word_count} words)")
    if word_count > 190:
        issues.append(f"email is over the PDF maximum ({word_count} words)")

    if any(phrase in lower_body or phrase in lower_subject for phrase in BANNED_PHRASES):
        issues.append("banned phrasing detected")

    if body.count("\n") < 5:
        issues.append("email needs more paragraph structure")

    if business_name and business_name.lower() not in lower_body:
        issues.append("business name missing from email")

    if confidence and str(confidence).upper() != "HIGH":
        issues.append("analysis confidence is not HIGH")

    selected_insight = selected_insight or ((analysis.get("insights") or [""])[0] if analysis.get("insights") else "")
    if selected_insight and not _insight_used(selected_insight, body):
        issues.append("selected insight is not clearly used")
    if selected_insight and is_repeated_insight(selected_insight):
        issues.append("selected insight was used recently")

    if persona_name and not _matches_persona_logic(body, persona_name):
        issues.append(f"{persona_name} logic is missing from the email")

    if hook_type and not _matches_hook(body, hook_type, competitor_names=competitor_names):
        issues.append(f"{hook_type} hook is not clear in the email")

    if not _has_soft_cta(body):
        issues.append("soft CTA missing")

    if any(marker in lower_body for marker in GENERIC_MARKERS):
        issues.append("email still reads as generic")

    return _dedupe(issues)


def is_bad(
    email,
    subject="",
    analysis=None,
    persona_name=None,
    business_name=None,
    hook_type=None,
    selected_insight=None,
    competitor_names=None,
    confidence=None,
):
    return bool(
        quality_issues(
            email,
            subject=subject,
            analysis=analysis,
            persona_name=persona_name,
            business_name=business_name,
            hook_type=hook_type,
            selected_insight=selected_insight,
            competitor_names=competitor_names,
            confidence=confidence,
        )
    )
