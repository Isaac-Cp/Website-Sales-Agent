import json
import re

import config


HOOK_TYPES = [
    "question",
    "contrarian",
    "observation",
    "competitor",
]


LEGACY_HOOK_MAP = {
    "question": "question",
    "contrarian": "contrarian",
    "data_observation": "observation",
    "mistake_callout": "contrarian",
    "competitor_comparison": "competitor",
    "observation": "observation",
    "competitor": "competitor",
}


EMAIL_SYSTEM_PROMPT = """You are an elite outreach strategist.

Use:
- Insights
- Persona
- Hook Type

Rules:
- Must use the selected HIGH-confidence insight
- Must follow persona logic
- Must use the selected hook type

Hook Types:
- Question
- Contrarian
- Observation
- Competitor

STRICT:
- No generic phrases
- Must feel human
- 120-180 words
- Must pass the uniqueness test

Return the email body only.
"""


SOFT_CTA_BY_HOOK = {
    "question": "If helpful, I can send the first two changes I would make.",
    "contrarian": "If useful, I can send the two fixes I would start with first.",
    "observation": "Happy to send a couple of quick notes on what I would adjust first.",
    "competitor": "Worth pointing out the first two gaps I would close?",
}


PERSONA_VALUE_LINES = {
    "Revenue Hacker": "For local service businesses, small friction at the first action usually costs the quote-ready traffic first.",
    "SEO Sniper": "When reviews are strong, the page has to cash that trust in quickly after the click or the search advantage gets wasted.",
    "CX Fixer": "When someone wants help quickly, even one extra beat in the contact path creates avoidable drop-off.",
    "Automation Operator": "Every extra step in the first contact path turns simple intent into unnecessary admin and follow-up.",
    "Authority Builder": "The reputation is already there, so the page should reinforce that specialist signal much faster.",
    "Competitor Spy": "In local markets, the business that makes the offer easiest to grasp usually wins the first call.",
}


GENERIC_PHRASES = [
    "quick look",
    "not clear",
    "improve your online presence",
    "help businesses grow",
]


def normalize_hook_type(hook_type):
    return LEGACY_HOOK_MAP.get((hook_type or "").strip().lower(), "observation")


def build_email_prompt(data, analysis, persona_name, persona_desc, hook_type, selected_insight, feedback=""):
    hook_type = normalize_hook_type(hook_type)
    feedback_block = f"\nREWRITE FEEDBACK:\n{feedback}\n" if feedback else ""
    review_intelligence = analysis.get("review_intelligence") or {}
    return f"""BUSINESS:
{data['name']} ({data['category']})
Location: {data['location']}
Greeting Name: {data['first_name']}

PERSONA:
{persona_name} -> {persona_desc}

SELECTED HIGH-CONFIDENCE INSIGHT:
{selected_insight}

SUPPORTING INSIGHTS:
{analysis.get('insights', [])}

PROBLEMS:
{analysis.get('problems', [])}

HOOK TYPE:
{hook_type}

REVIEW INTELLIGENCE:
Positive: {review_intelligence.get('positive', 'No review positives were captured.')}
Negative: {review_intelligence.get('negative', 'No review complaints were captured.')}
Patterns: {review_intelligence.get('patterns', 'No review patterns were captured.')}

COMPETITOR CONTEXT:
{data['competitors_text']}

SOURCE EVIDENCE:
{data['evidence_text']}{feedback_block}

RULES:
1. Use only the selected hook type.
2. Use the selected HIGH-confidence insight directly.
3. Follow the persona logic, not just the persona label.
4. Make the email feel handwritten and specific to this business.
5. Keep it between 120 and 180 words.
6. No generic phrases like "quick look", "not clear", or "improve your online presence".
7. Pass the uniqueness test: if this could go to another business unchanged, rewrite it.

STRUCTURE:
Hi [Name],
[Personalized hook]
[Insight paragraph]
[Value paragraph]
[Soft CTA]
Best,
[Your Name]

OUTPUT:
Email only
"""


def _strip_code_fences(text):
    value = (text or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:text|json)?", "", value).strip()
        value = re.sub(r"```$", "", value).strip()
    return value


def extract_email_body(content):
    value = _strip_code_fences(content)
    if not value:
        return ""

    if value.startswith("{") and value.endswith("}"):
        try:
            parsed = json.loads(value)
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            value = str(parsed.get("email") or parsed.get("body") or "").strip()

    lines = []
    for raw_line in value.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        if line.lower().startswith("subject:"):
            continue
        if any(phrase in line.lower() for phrase in GENERIC_PHRASES):
            line = line.replace("quick look", "first pass")
            line = line.replace("not clear", "harder to spot")
            line = line.replace("improve your online presence", "tighten the first impression")
        lines.append(line)

    text = "\n".join(lines).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _sender_name():
    name = str(getattr(config, "SENDER_NAME", "") or "").strip()
    return name or "Your Name"


def build_soft_cta(hook_type):
    return SOFT_CTA_BY_HOOK.get(normalize_hook_type(hook_type), SOFT_CTA_BY_HOOK["observation"])


def build_subject_line(business_name, hook_type, selected_insight=""):
    del selected_insight
    business_name = str(business_name or "your business").strip()
    hook = normalize_hook_type(hook_type)
    if hook == "question":
        subject = f"Quick question for {business_name}"
    elif hook == "contrarian":
        subject = f"Quick thought on {business_name}"
    elif hook == "competitor":
        subject = f"Quick note on {business_name}"
    else:
        subject = f"Small thing I noticed at {business_name}"
    return subject[:80].strip()


def _split_long_paragraphs(lines, limit=26):
    rebuilt = []
    for line in lines:
        words = line.split()
        if len(words) <= limit:
            rebuilt.append(line)
            continue
        midpoint = max(12, len(words) // 2)
        rebuilt.append(" ".join(words[:midpoint]))
        rebuilt.append(" ".join(words[midpoint:]))
    return rebuilt


def finalize_email_body(email_text, first_name=None, hook_type="observation"):
    body = extract_email_body(email_text)
    lines = [line.strip() for line in body.split("\n") if line.strip()]

    greeting = f"Hi {first_name or 'there'},"
    if not lines or not lines[0].lower().startswith("hi "):
        lines.insert(0, greeting)

    lines = _split_long_paragraphs(lines)

    joined = "\n\n".join(lines).lower()
    if (
        "if helpful, i can send" not in joined
        and "if useful, i can send" not in joined
        and "happy to send" not in joined
        and "worth pointing out" not in joined
    ):
        lines.append(build_soft_cta(hook_type))

    sender_name = _sender_name()
    final_text = "\n\n".join(lines)
    lower_final = final_text.lower()
    if "best," not in lower_final and "best regards," not in lower_final:
        final_text = final_text.rstrip() + f"\n\nBest,\n{sender_name}"
    elif sender_name.lower() not in lower_final:
        final_text = final_text.rstrip() + f"\n{sender_name}"

    return re.sub(r"\n{3,}", "\n\n", final_text).strip()


def _hook_line(hook_type, business_name, selected_insight, competitors=None):
    hook = normalize_hook_type(hook_type)
    insight = str(selected_insight or "the first contact step is harder to spot than it should be").rstrip(".")
    competitors = competitors or []
    competitor_name = ""
    for competitor in competitors:
        if isinstance(competitor, dict) and competitor.get("business_name"):
            competitor_name = competitor["business_name"]
            break

    if hook == "question":
        return f"Have you already looked at how this comes across on the site for {business_name}: {insight.lower()}?"
    if hook == "contrarian":
        return f"The issue probably is not awareness. It is that {insight.lower()}."
    if hook == "competitor" and competitor_name:
        return f"A nearby competitor like {competitor_name} raises the bar because {insight.lower()}."
    if hook == "competitor":
        return f"The local comparison gets tougher when {insight.lower()}."
    return f"One thing that stood out was {insight.lower()}."


def build_fallback_email(lead_data, analysis, persona_name, hook_type, selected_insight):
    business_name = lead_data.get("business_name") or "your business"
    first_name = lead_data.get("first_name") or "there"
    city = lead_data.get("city") or "your area"
    industry = lead_data.get("industry") or "local service business"
    competitors = lead_data.get("competitors") or []
    value_line = PERSONA_VALUE_LINES.get(
        persona_name,
        "A small fix to the first decision step usually changes how many good enquiries actually come through.",
    )
    insight = str(selected_insight or "the first contact step is harder to spot than it should be").rstrip(".")
    problem = ""
    problems = analysis.get("problems") or []
    if problems:
        problem = str(problems[0]).rstrip(".")

    email_text = "\n\n".join(
        [
            f"Hi {first_name},",
            f"I was looking through {industry} businesses in {city}, and {business_name} stood out because the underlying demand already seems to be there.",
            _hook_line(hook_type, business_name, insight, competitors),
            f"The main thing I would act on first is {insight.lower()}. {problem or 'That is usually where strong intent starts leaking away.'}",
            value_line,
            build_soft_cta(hook_type),
            f"Best,\n{_sender_name()}",
        ]
    )
    return finalize_email_body(email_text, first_name=first_name, hook_type=hook_type)
