import json

from ai.analysis_engine import ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt, build_review_intelligence
from ai.email_engine import (
    EMAIL_SYSTEM_PROMPT,
    HOOK_TYPES,
    build_email_prompt,
    build_fallback_email,
    build_subject_line,
    finalize_email_body,
    normalize_hook_type,
)
from ai.persona_engine import get_persona
from ai.quality_filter import is_repeated_insight, quality_issues, remember_insight


def _legacy():
    import llm_helper as legacy

    return legacy


def _trim_text(value, limit=280):
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace("\r", "\n").split("\n") if part.strip()]
        return parts or [value.strip()]
    return [str(value).strip()]


def _call_llm_json(system_prompt, user_prompt, llm=None, temperature=0.25, max_tokens=800):
    legacy = _legacy()

    if llm is not None:
        provider = "custom"
        try:
            response = llm(system_prompt=system_prompt, user_prompt=user_prompt)
        except TypeError:
            try:
                response = llm(system_prompt, user_prompt)
            except TypeError:
                response = llm({"system_prompt": system_prompt, "user_prompt": user_prompt})
        if isinstance(response, dict):
            return response, provider
        return legacy._extract_json_payload(str(response)), provider

    content, provider = legacy._run_elite_llm(
        system_prompt,
        user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return legacy._extract_json_payload(content), provider


def _call_llm_text(system_prompt, user_prompt, llm=None, temperature=0.75, max_tokens=900):
    legacy = _legacy()

    if llm is not None:
        provider = "custom"
        try:
            response = llm(system_prompt=system_prompt, user_prompt=user_prompt)
        except TypeError:
            try:
                response = llm(system_prompt, user_prompt)
            except TypeError:
                response = llm({"system_prompt": system_prompt, "user_prompt": user_prompt})
        if isinstance(response, dict):
            return str(response.get("email") or response.get("body") or json.dumps(response)), provider
        return str(response), provider

    content, provider = legacy._run_elite_llm(
        system_prompt,
        user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return str(content), provider


def _build_analysis_input(lead_data, prompt_payload):
    website_signals = prompt_payload.get("website_signals") or {}
    review_intelligence = build_review_intelligence(prompt_payload.get("reviews") or [])

    website_lines = []
    for label, value in [
        ("Headline", website_signals.get("headline")),
        ("Page title", website_signals.get("page_title")),
        ("Meta description", website_signals.get("meta_description")),
        ("Homepage summary", website_signals.get("homepage_summary")),
    ]:
        if value:
            website_lines.append(f"{label}: {value}")
    if website_signals.get("services"):
        website_lines.append("Services: " + ", ".join(website_signals["services"][:6]))
    if website_signals.get("cta_labels"):
        website_lines.append("CTA labels: " + ", ".join(website_signals["cta_labels"][:5]))
    if website_signals.get("trust_markers"):
        website_lines.append("Trust markers: " + ", ".join(website_signals["trust_markers"][:5]))
    if prompt_payload.get("audit_issues"):
        website_lines.append("Audit issues: " + "; ".join(prompt_payload["audit_issues"][:6]))

    review_lines = [review for review in (prompt_payload.get("reviews") or []) if review]
    competitor_lines = []
    for competitor in prompt_payload.get("competitors") or []:
        name = competitor.get("business_name")
        if not name:
            continue
        rating = competitor.get("rating")
        website = competitor.get("website")
        details = []
        if rating is not None:
            details.append(f"{rating} stars")
        if website:
            details.append(website)
        suffix = f" ({', '.join(details)})" if details else ""
        competitor_lines.append(f"{name}{suffix}")

    return {
        "name": prompt_payload.get("business_name") or "Unknown business",
        "category": prompt_payload.get("industry") or "local service business",
        "location": prompt_payload.get("city") or "Unknown location",
        "rating": prompt_payload.get("rating") if prompt_payload.get("rating") is not None else "N/A",
        "reviews": prompt_payload.get("review_count") if prompt_payload.get("review_count") is not None else 0,
        "first_name": prompt_payload.get("first_name") or "there",
        "website_text": "\n".join(website_lines) or "No website evidence available.",
        "reviews_text": "\n".join(review_lines) or "No review snippets available.",
        "competitors_text": "\n".join(competitor_lines) or "No competitor context available.",
        "evidence_text": "\n".join(f"- {item}" for item in (prompt_payload.get("evidence") or [])) or "- No evidence captured.",
        "review_intelligence": review_intelligence,
    }


def _classify_angle(text):
    lower = (text or "").lower()
    if any(token in lower for token in ["competitor", "compared", "versus", "local market"]):
        return "competitor"
    if any(token in lower for token in ["review", "reviews", "rating", "google", "maps", "trust"]):
        return "reviews"
    if any(token in lower for token in ["form", "book", "booking", "call", "contact", "button", "mobile", "homepage", "page"]):
        return "ux"
    return "revenue"


def _select_diverse_items(items, limit=3):
    selected = []
    fallback = []
    seen_text = set()
    seen_angles = set()

    for item in items:
        cleaned = _trim_text(str(item or "").strip().rstrip("."), 220)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen_text:
            continue
        seen_text.add(key)
        angle = _classify_angle(cleaned)
        if angle in seen_angles:
            fallback.append(cleaned)
            continue
        seen_angles.add(angle)
        selected.append(cleaned)
        if len(selected) >= limit:
            return selected

    for item in fallback:
        if item not in selected:
            selected.append(item)
        if len(selected) >= limit:
            break

    return selected[:limit]


def _problem_bank(prompt_payload):
    website_signals = prompt_payload.get("website_signals") or {}
    review_count = prompt_payload.get("review_count")
    rating = prompt_payload.get("rating")
    competitors = prompt_payload.get("competitors") or []
    pagespeed_score = prompt_payload.get("pagespeed_score")

    problems = []
    for issue in prompt_payload.get("audit_issues") or []:
        problems.append(issue)

    if website_signals.get("cta_visibility") == "unclear":
        problems.append("The homepage does not make the first next step obvious enough for a high-intent visitor.")
    if website_signals.get("contact_method") == "form":
        problems.append("The main contact path leans on a form, which adds friction when someone wants a fast response.")
    if rating and review_count:
        problems.append("Strong review proof exists, but the site still has to convert that trust into action more clearly.")
    if competitors:
        competitor_name = competitors[0].get("business_name")
        if competitor_name:
            problems.append(f"A competitor like {competitor_name} gives buyers another nearby option if the offer is clearer there.")
    if pagespeed_score is not None:
        try:
            if float(pagespeed_score) < 0.75:
                problems.append("The site speed likely makes the first impression work harder than it should.")
        except Exception:
            pass
    if not problems:
        problems.append("The digital experience is not carrying the strongest proof points into the first decision moment.")

    return problems


def _insight_bank(prompt_payload, analysis_input):
    website_signals = prompt_payload.get("website_signals") or {}
    review_intelligence = analysis_input.get("review_intelligence") or {}
    rating = prompt_payload.get("rating")
    review_count = prompt_payload.get("review_count")
    competitors = prompt_payload.get("competitors") or []

    insights = []
    if website_signals.get("cta_visibility") == "unclear":
        insights.append("The homepage is making visitors think too hard about the next step instead of pointing them toward one obvious action.")
    if website_signals.get("contact_method") == "form":
        insights.append("The site appears to rely on a form first, which is a slow path for people who are ready to call now.")
    if rating and review_count:
        insights.append(f"The business already has {rating} stars across {review_count} reviews, so the page should cash that trust in faster after the click.")
    positive_review = review_intelligence.get("positive")
    if positive_review and "No review" not in positive_review:
        insights.append(f"Review language suggests real trust signals are present already: {positive_review.rstrip('.')}.")
    negative_review = review_intelligence.get("negative")
    if negative_review and "No repeated complaints" not in negative_review:
        insights.append(f"Review complaints point to buyer sensitivity around experience: {negative_review.rstrip('.')}.")
    if competitors:
        competitor_name = competitors[0].get("business_name")
        if competitor_name:
            insights.append(f"A nearby competitor like {competitor_name} means clarity matters on first view because buyers have a fast comparison point.")
    if prompt_payload.get("evidence"):
        insights.append(f"One strong proof point already exists in the evidence bank: {prompt_payload['evidence'][0].rstrip('.')}.")
    if not insights:
        insights.append("The strongest opportunity is tightening the first impression so the best intent does not stall before contact.")

    return insights


def _normalize_confidence(value, prompt_payload, insights):
    normalized = str(value or "").strip().upper()
    if normalized not in {"HIGH", "MEDIUM", "LOW"}:
        evidence_sources = 0
        if prompt_payload.get("website_signals"):
            evidence_sources += 1
        if prompt_payload.get("reviews"):
            evidence_sources += 1
        if prompt_payload.get("competitors"):
            evidence_sources += 1
        if prompt_payload.get("audit_issues"):
            evidence_sources += 1

        if evidence_sources >= 3 and len(insights) >= 3:
            return "HIGH"
        if evidence_sources >= 2:
            return "MEDIUM"
        return "LOW"

    if normalized == "HIGH" and len(insights) < 3:
        return "MEDIUM"
    return normalized


def _normalize_analysis(parsed, prompt_payload, analysis_input, provider):
    parsed_problems = _as_list(parsed.get("problems"))
    parsed_insights = _as_list(parsed.get("insights") or parsed.get("observations"))

    problems = _select_diverse_items(parsed_problems + _problem_bank(prompt_payload), limit=3)
    insights = _select_diverse_items(parsed_insights + _insight_bank(prompt_payload, analysis_input), limit=3)
    confidence = _normalize_confidence(parsed.get("confidence"), prompt_payload, insights)

    return {
        "problems": problems,
        "insights": insights,
        "observations": insights,
        "confidence": confidence,
        "review_intelligence": analysis_input.get("review_intelligence") or {},
        "provider": provider,
    }


def _fallback_analysis(prompt_payload, analysis_input):
    insights = _select_diverse_items(_insight_bank(prompt_payload, analysis_input), limit=3)
    return {
        "problems": _select_diverse_items(_problem_bank(prompt_payload), limit=3),
        "insights": insights,
        "observations": insights,
        "confidence": _normalize_confidence("", prompt_payload, insights),
        "review_intelligence": analysis_input.get("review_intelligence") or {},
        "provider": "fallback",
    }


def _preferred_pdf_hook(prompt_payload, persona_name):
    legacy_hook = _legacy()._preferred_hook_type(prompt_payload, persona_name)
    return normalize_hook_type(legacy_hook)


def _hook_for_attempt(preferred_hook, attempt):
    if preferred_hook in HOOK_TYPES:
        start = HOOK_TYPES.index(preferred_hook)
    else:
        start = 0
    return HOOK_TYPES[(start + attempt) % len(HOOK_TYPES)]


def _available_hooks(lead_data, preferred_hook):
    hooks = list(HOOK_TYPES)
    if not (lead_data.get("competitors") or []):
        hooks = [hook for hook in hooks if hook != "competitor"]
    if preferred_hook in hooks:
        hooks.remove(preferred_hook)
        hooks.insert(0, preferred_hook)
    return hooks or ["observation"]


def _select_insight(analysis, attempt=0):
    insights = list(analysis.get("insights") or analysis.get("observations") or [])
    if not insights:
        return ""

    offset = attempt % len(insights)
    rotated = insights[offset:] + insights[:offset]
    for insight in rotated:
        if not is_repeated_insight(insight):
            return insight
    return rotated[0]


def _normalize_email_result(email_text, lead_data, analysis, persona_name, hook_type, selected_insight, provider):
    business_name = lead_data.get("business_name") or "your business"
    final_body = finalize_email_body(
        email_text,
        first_name=lead_data.get("first_name"),
        hook_type=hook_type,
    )
    return {
        "persona": persona_name,
        "hook_type": hook_type,
        "observations": analysis.get("insights") or [],
        "insights": analysis.get("insights") or [],
        "problems": analysis.get("problems") or [],
        "confidence": analysis.get("confidence"),
        "strategy": f"Use a {hook_type} hook and the {persona_name.lower()} angle around one high-confidence insight.",
        "insight": selected_insight,
        "selected_insight": selected_insight,
        "subject": build_subject_line(business_name, hook_type, selected_insight),
        "email": final_body,
        "provider": provider,
        "analysis_provider": analysis.get("provider"),
        "review_intelligence": analysis.get("review_intelligence") or {},
    }


def _email_quality_issues(result, analysis, lead_data):
    competitor_names = []
    for competitor in lead_data.get("competitors") or []:
        if isinstance(competitor, dict):
            name = competitor.get("business_name")
        else:
            name = competitor
        if name:
            competitor_names.append(name)

    return quality_issues(
        result.get("email") or "",
        subject=result.get("subject") or "",
        analysis=analysis,
        persona_name=result.get("persona"),
        business_name=lead_data.get("business_name"),
        hook_type=result.get("hook_type"),
        selected_insight=result.get("insight"),
        competitor_names=competitor_names,
        confidence=analysis.get("confidence"),
    )


def _fallback_result(lead_data, analysis, persona_name, hook_type):
    selected_insight = _select_insight(analysis, 0) or "the first contact step is harder to spot than it should be"
    body = build_fallback_email(lead_data, analysis, persona_name, hook_type, selected_insight)
    result = {
        "persona": persona_name,
        "hook_type": hook_type,
        "observations": analysis.get("insights") or [],
        "insights": analysis.get("insights") or [],
        "problems": analysis.get("problems") or [],
        "confidence": analysis.get("confidence"),
        "strategy": f"Fallback note built around a {hook_type} hook and the strongest available insight.",
        "insight": selected_insight,
        "selected_insight": selected_insight,
        "subject": build_subject_line(lead_data.get("business_name"), hook_type, selected_insight),
        "email": body,
        "provider": "fallback",
        "analysis_provider": analysis.get("provider"),
        "review_intelligence": analysis.get("review_intelligence") or {},
    }
    remember_insight(selected_insight)
    return result


def run_pipeline(lead_data, llm=None, country=None, max_retries=3):
    del country
    legacy = _legacy()
    prompt_payload = legacy._build_elite_prompt_payload(lead_data)
    analysis_input = _build_analysis_input(lead_data, prompt_payload)
    preferred_persona = legacy._default_elite_persona(lead_data)
    persona_name, persona_desc = get_persona(
        preferred=preferred_persona,
        seed_text=prompt_payload.get("business_name"),
    )
    preferred_hook = _preferred_pdf_hook(prompt_payload, persona_name)
    available_hooks = _available_hooks(lead_data, preferred_hook)

    try:
        analysis_prompt = build_analysis_prompt(analysis_input, persona_name, persona_desc)
        parsed_analysis, analysis_provider = _call_llm_json(
            ANALYSIS_SYSTEM_PROMPT,
            analysis_prompt,
            llm=llm,
            temperature=0.2,
            max_tokens=700,
        )
        analysis = _normalize_analysis(parsed_analysis, prompt_payload, analysis_input, analysis_provider)
    except Exception as exc:
        print(f"[Analysis Engine] Falling back due to: {exc}")
        analysis = _fallback_analysis(prompt_payload, analysis_input)

    feedback = ""
    for attempt in range(max_retries):
        hook_type = available_hooks[attempt % len(available_hooks)]
        selected_insight = _select_insight(analysis, attempt)

        try:
            email_prompt = build_email_prompt(
                analysis_input,
                analysis,
                persona_name,
                persona_desc,
                hook_type,
                selected_insight,
                feedback=feedback,
            )
            raw_email, email_provider = _call_llm_text(
                EMAIL_SYSTEM_PROMPT,
                email_prompt,
                llm=llm,
                temperature=0.75,
                max_tokens=950,
            )
            result = _normalize_email_result(
                raw_email,
                lead_data,
                analysis,
                persona_name,
                hook_type,
                selected_insight,
                email_provider,
            )
            issues = _email_quality_issues(result, analysis, lead_data)
            if not issues:
                remember_insight(result["insight"])
                result["provider"] = f"{analysis.get('provider')}+{email_provider}"
                return result

            feedback = "Previous draft failed these checks: " + "; ".join(issues)
            print(f"[Email Engine] Retry {attempt + 1}/{max_retries}: {feedback}")
        except Exception as exc:
            feedback = f"Previous draft failed due to: {exc}"
            print(f"[Email Engine] Attempt {attempt + 1}/{max_retries} failed: {exc}")

    return _fallback_result(lead_data, analysis, persona_name, available_hooks[0])
