try:
    from groq import Groq
except Exception:
    Groq = None
import config
import os
import random
import json
import math
import re

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def _get_country_config(country):
    c = (country or "AU").upper()
    if c == "EU" or c == "UK":
        return {
            "tone": "Polite and reserved",
            "avoid": "hype, urgency, 'boost', 'scale', 'grow'",
            "buffer": "It might be worth considering...",
            "style": "No hype, use 'might help' or 'often helps'."
        }
    elif c == "US":
        return {
            "tone": "Friendly and direct",
            "avoid": "Apologetic language, over-softening, long explanations.",
            "buffer": "One thing I noticed is...",
            "style": "Slightly conversational, clear value."
        }
    else: # Default to AU
        return {
            "tone": "Casual but professional",
            "avoid": "Corporate language, formal phrasing, sales enthusiasm.",
            "buffer": "One thing I noticed is",
            "style": "Short sentences, low ego."
        }

# --- Spintax Master Templates ---
MASTER_SUBJECT_TEMPLATES = [
    "Question regarding {the|your} {business_name} website",
    "Quick {suggestion|idea} for {business_name}",
    "{Feedback|Thought} on your {city} Google Maps listing",
    "Improvement for {business_name}",
    "Regarding your {online presence|site} in {city}"
]

MASTER_BODY_TEMPLATE = (
    "{Hi|Hello|Hey} {first_name|there|{business_name} team},\n\n"
    "I was {browsing|looking at|researching} {local {industry} pros|businesses} in {city} "
    "and {found|came across} your profile. {Great work on the reviews|You have a solid reputation}!\n\n"
    "I noticed your website {could be converting more customers|is a bit slow on mobile|needs a modern touch}. "
    "I specialize in {website redesigns|web development} specifically for {industry} companies to help "
    "{increase your booking rate|get you more calls}.\n\n"
    "Would you be {open to|interested in} a quick {suggestion|screenshot} of how to fix this?\n\n"
    "Best,\n{sender_name}"
)

def _get_fallback_subject(business_name):
    """Simple fallback subject if LLM fails."""
    return f"Question regarding {business_name}"

def _enforce_rules(subject, body, business_name, trade, city, first_name):
    """Enforce sanity rules on the generated body."""
    # Ensure business name is present
    if business_name.lower() not in body.lower():
        body = f"I was looking into {business_name} in {city} and...\n\n" + body
    
    # Ensure no placeholder brackets
    body = body.replace("[business_name]", business_name).replace("[trade]", trade).replace("[city]", city)
    body = body.replace("[First Name]", first_name or "there").replace("[Your Name]", config.SENDER_NAME)
    
    return body

def _fix_subject(subject, business_name):
    """Clean up any LLM weirdness in subject."""
    subject = subject.strip().strip('"').strip("'")
    if "Subject:" in subject:
        subject = subject.replace("Subject:", "").strip()
    return subject

def generate_spintax_email(business_name, city, industry, first_name=None):
    """
    Generates a highly randomized email using the Master Spintax Template.
    """
    try:
        import spintax
    except ImportError:
        return f"Quick idea for {business_name}", f"Hi {first_name or 'there'},\n\nI found {business_name} on Google Maps..."

    # 1. Generate Subject
    raw_subject = random.choice(MASTER_SUBJECT_TEMPLATES)
    subject = spintax.spin(raw_subject)
    subject = subject.replace("{business_name}", business_name).replace("{city}", city)

    # 2. Master Spintax Body
    body = spintax.spin(MASTER_BODY_TEMPLATE)
    body = body.replace("{business_name}", business_name).replace("{city}", city).replace("{industry}", industry)
    body = body.replace("{first_name}", first_name if first_name else "there")
    body = body.replace("{sender_name}", config.SENDER_NAME)
    
    return subject, body

def _validate_email_content(subject, body, business_name, trade):
    """
    Returns (bool, reason) - True if valid, False if rejected.
    Uses scoring engine (0-100).
    """
    score = 0
    reason_list = []
    
    # 1. Length Check (15 pts)
    # Max 110 words
    words = len(body.split())
    if words <= 110:
        score += 15
    else:
        reason_list.append(f"Length issue ({words} words > 110)")
        
    # 2. Observable Detail (25 pts)
    obs_score = _score_personalization(body)
    if obs_score >= 2:
        score += 25
    else:
        reason_list.append("Missing observable detail")
        
    # 3. Generic Phrase / Marketing Language Check (20 pts)
    generic_phrases = [
        "has a lot to offer",
        "improving visitor experience",
        "boost inquiries",
        "optimize conversions",
        "your website could benefit",
        "i specialize in helping businesses",
        "strong reputation",
        "great website",
        "lot to offer",
        "optimize", "boost", "scale", "conversion", "marketing"
    ]
    found_generic = [p for p in generic_phrases if p in body.lower()]
    if not found_generic:
        score += 20
    else:
        reason_list.append(f"Generic/Marketing phrases found: {', '.join(found_generic)}")

    # 4. Industry Alignment (15 pts)
    # Mentions industry-specific action (call/book/emergency)
    trade_lower = trade.lower()
    industry_keywords = []
    if "plumb" in trade_lower:
        industry_keywords = ["emergency", "leak", "hot water", "blocked", "drain"]
    elif "hvac" in trade_lower:
        industry_keywords = ["heating", "cooling", "ac", "furnace", "air con"]
    elif "garage" in trade_lower:
        industry_keywords = ["door", "spring", "opener", "repair"]
    
    # Also generic industry actions
    industry_actions = ["call", "book", "schedule", "quote", "emergency"]
    
    if any(k in body.lower() for k in industry_keywords) or any(k in body.lower() for k in industry_actions):
        score += 15
    else:
        reason_list.append("No industry alignment")
        
    # 5. CTA Quality (15 pts)
    # MUST BE REPLY-BASED (No calls)
    # "send over", "reply yes", "share ideas", "no call needed"
    cta_lower = body.lower()
    
    # Penalize Call CTAs
    call_triggers = ["5-minute call", "quick call", "hop on a call", "zoom", "meeting", "schedule"]
    found_call = [c for c in call_triggers if c in cta_lower and "no call needed" not in cta_lower]
    
    if found_call:
        return False, f"HARD FAIL: Call CTA detected ({found_call[0]}). Must be reply-based."
        
    if _has_low_friction_cta(cta_lower):
        score += 15
    else:
        reason_list.append("Weak CTA (must be low-friction reply request)")
        
    # 6. Subject Quality (10 pts)
    if not any(w in subject.lower() for w in ["improving", "optimizing", "enhancing", "marketing", "sales"]):
        score += 10
    else:
        reason_list.append("Subject too corporate")
        
    # AUTO-REJECT LOGIC
    # Hard Fails
    if obs_score < 2:
        return False, "HARD FAIL: No observable detail."
    
    if found_generic:
        return False, f"HARD FAIL: Generic/Marketing phrases detected: {found_generic[0]}"
        
    # Heuristic for "more than one suggestion": count "could" or "should" or list items?
    # The prompt says "Make only ONE suggestion".
    # We can check for multiple bullet points or multiple sentences with "can help".
    if body.count("can help") > 1 or body.count("might help") > 1:
         return False, "HARD FAIL: More than one suggestion detected."

    if score < 80:
        return False, f"Score {score}/100. Issues: {'; '.join(reason_list)}"
    
    return True, f"Valid (Score {score})"

QA_FORBIDDEN_PHRASES = [
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

def check_qa(subject, body, persona=None):
    """
    Returns (passed, score, issues)
    """
    passed = True
    issues = []
    score = 100
    
    # 1. Forbidden phrases
    found_forbidden = [p for p in QA_FORBIDDEN_PHRASES if p.lower() in body.lower()]
    if found_forbidden:
        passed = False
        score -= len(found_forbidden) * 20
        issues.append(f"Forbidden phrases: {', '.join(found_forbidden)}")
        
    # 2. Personalization score
    p_score = _score_personalization(body)
    if p_score < 2:
        passed = False
        score -= 30
        issues.append("Low personalization score")
        
    # 3. Persona consistency
    if persona:
        p_lower = persona.lower()
        # Simple check: Casual persona should not use formal sign-offs
        if "casual" in p_lower and any(f in body.lower() for f in ["sincerely", "best regards", "to whom"]):
            passed = False
            score -= 20
            issues.append("Persona inconsistency (Casual vs Formal)")
            
    # 4. Length check
    words = len(body.split())
    if words > 120:
        passed = False
        score -= 20
        issues.append(f"Too long ({words} words)")
        
    return passed, max(0, score), issues

def _get_cta_text(business_name, industry, issue_type="general"):
    """
    Selects a low-friction CTA with stable variation so drafts do not all end
    with the same ask.
    """
    i = (industry or "").lower()
    it = (issue_type or "").lower()
    bn = business_name or "your team"

    visual_ctas = [
        "If helpful, I can send a marked-up screenshot of the first thing I would change.",
        "If useful, I can point to the first two spots I would tighten up on the page.",
        "Happy to send the two fixes I would start with on the homepage.",
    ]
    automation_ctas = [
        "If useful, I can send the two places where I would remove the extra back-and-forth.",
        "Happy to send the first two changes I would make to cut the admin friction.",
    ]
    competitor_ctas = [
        f"If helpful, I can point out the gap I would close first for {bn}.",
        "Worth pointing out the first two changes I would make on that front?",
    ]
    default_ctas = [
        f"If useful, I can send over the first two changes I would make for {bn}.",
        "Happy to send the two fixes I would start with.",
        "Worth pointing out the two places I would clean up first?",
        "If helpful, I can send a couple of quick notes on what I would adjust first.",
    ]

    if any(token in it for token in ["mobile", "button", "form", "visible", "layout", "headline"]):
        return _stable_choice(visual_ctas, bn, i, it)
    if any(token in it for token in ["manual", "follow-up", "follow up", "admin", "wasted"]):
        return _stable_choice(automation_ctas, bn, i, it)
    if any(token in it for token in ["competitor", "gap", "versus", "local market"]):
        return _stable_choice(competitor_ctas, bn, i, it)
    return _stable_choice(default_ctas, bn, i, it)

def _score_personalization(body):
    """
    Scoring:
    +2 observable website behavior (phone, mobile, button, scroll, form, call)
    +1 industry-specific insight (garage, hvac, plumbing specific terms)
    -2 generic phrasing
    -3 assumptions without proof
    """
    score = 0
    b = body.lower()
    
    # Observable behavior keywords
    observables = [
        "phone number", "mobile view", "scroll", "call button", "contact form", "booking", "click", "visible", "tap-to-call", "above the fold",
        "slow", "loading", "speed", "fast", "broken", "link", "error", "404", "page", "dead end"
    ]
    if any(o in b for o in observables):
        score += 2
        
    # Industry specific (simple check)
    industry_terms = ["emergency", "after-hours", "service page", "quote", "schedule", "leak", "hot water", "heating", "cooling", "door", "spring"]
    if any(i in b for i in industry_terms):
        score += 1
        
    # Generic phrasing penalty
    generics = ["structure", "user experience", "interface", "layout", "strong brand"]
    if any(g in b for g in generics):
        score -= 2
        
    return score

def generate_reply_response(reply_type, context_data):
    """
    Generates a response based on the reply type.
    reply_type: "interested", "maybe", "how_found", "objection", "defensive"
    """
    rt = (reply_type or "").lower()
    
    if "interested" in rt or "yes" in rt:
        return (
            "Thanks for the reply — appreciate it.\n"
            "I can keep it very short and focused.\n"
            "I’ll send those ideas over in a separate email shortly."
        )
    
    if "maybe" in rt or "not now" in rt:
        return (
            "Totally understand.\n"
            "If it helps, I can also just send over the idea in a sentence or two.\n"
            "Either way is fine."
        )
        
    if "found" in rt or "how did you" in rt:
        service = context_data.get('industry', 'service')
        return (
            f"I was looking at a few local {service} businesses and your site stood out.\n"
            "I usually do a quick manual check before reaching out."
        )
        
    if "objection" in rt or "already have" in rt:
        return (
            "That makes sense.\n"
            "I’ll step back — appreciate you letting me know.\n"
            "Wishing you all the best."
        )
        
    if "defensive" in rt or "confused" in rt:
        return (
            "Sorry if it came across the wrong way — not a pitch.\n"
            "Just wanted to share a quick observation.\n"
            "Happy to leave it there."
        )
        
    return "Thanks for getting back to me." # Fallback

def _detect_service(business_name, industry):
    """
    Enforces the Industry Accuracy Guard.
    IF business_name contains "Plumbing" → default service = plumbing.
    """
    bn = (business_name or "").lower()
    if "plumbing" in bn:
        return "plumbing"
    return industry

def _choose_problem_context(audit_issues):
    """
    Maps audit issues to the user's requested problem/fix structure.
    Returns (specific_issue, quick_fix)
    """
    if not audit_issues:
        return (
            "the homepage does not make the first contact step easy to spot",
            "making the primary contact action stand out faster"
        )

    s = " ".join(a.lower() for a in audit_issues)
    
    # 1. Mobile / Viewport
    if "viewport" in s or "mobile" in s:
        return (
            "the mobile view didn't feel fully optimized for quick booking",
            "optimizing mobile load speed and adding a clear 'Call Now' button"
        )
    
    # 2. SSL / Security
    if "https" in s or "secure" in s or "ssl" in s:
        return (
            "the site didn't seem to use a secure connection (HTTPS), which lowers trust",
            "enabling HTTPS and showing trust badges near the contact button"
        )
    
    # 3. Speed (New)
    if "slow" in s or "load time" in s:
        return (
            "the page took a bit longer to load than usual (over 3-4 seconds)",
            "optimizing image sizes or checking the hosting speed"
        )

    # 4. Broken Links (New)
    if "broken" in s or "dead" in s or "link" in s:
        return (
            "I clicked a few links and hit a dead end (broken pages)",
            "doing a quick scan to fix broken paths so visitors don't get frustrated"
        )
        
    # 5. Title / SEO / Clarity
    if "title" in s:
        return (
            "the page didn’t immediately communicate what to do next",
            "adding a clear headline and a single primary call to action"
        )

    return (
        "the site makes the contact path do more work than it should",
        "bringing the primary contact action forward"
    )

def _industry_tip(industry):
    """
    Returns an industry-specific observation library tip.
    """
    i = (industry or "").lower()
    
    # PLUMBER OBSERVATIONS
    if "plumb" in i:
        opts = [
            "Phone number not visible without scrolling",
            "Emergency call option not obvious",
            "Booking action buried in menu",
            "Mobile tap-to-call missing",
            "No clear next step on homepage"
        ]
        return random.choice(opts)
        
    # HVAC OBSERVATIONS
    if "hvac" in i or "air" in i or "heat" in i:
        opts = [
            "No clear emergency or same-day option",
            "Call button not visible above the fold",
            "Service areas not obvious on first view",
            "Mobile booking requires multiple steps",
            "No seasonal service callout"
        ]
        return random.choice(opts)
        
    # GARAGE DOOR OBSERVATIONS
    if "garage" in i or "door" in i:
        opts = [
            "Emergency repair option not highlighted",
            "Call button blends into header",
            "Booking option unclear on mobile",
            "After-hours contact not obvious",
            "Primary action not clear on first view"
        ]
        return random.choice(opts)
        
    # Default Fallback
    return "making contact options easier to spot"

def _compose_observation(signals, country="AU"):
    config_data = _get_country_config(country)
    buffer = config_data.get("buffer", "One thing I noticed is")
    
    if not signals.get("website_exists", True):
        return f"{buffer} it looks like customers may not find a website quickly"
    
    cta = (signals.get("cta_visibility") or "").lower()
    if cta in ("unclear", "missing"):
        return f"{buffer} the homepage does not make the main contact action obvious"
    
    if signals.get("website_mobile_friendly") is False:
        return f"{buffer} mobile visitors may leave because key actions aren’t easy to find"
        
    return f"{buffer} the first contact path is doing more work than it needs to"

def _compose_trust_line(signals):
    rating = signals.get("google_rating")
    reviews_present = signals.get("reviews_present", False)
    if isinstance(rating, (int, float)) and rating >= 4.5:
        return "it seems your strong reputation isn’t fully reflected in how people reach you online"
    if not reviews_present:
        return ""
    if reviews_present and (rating is None or rating == 0):
        return "you appear to have a solid local presence"
    return ""

def _sanitize_language(text):
    if not text:
        return ""
    repl = {
        "boost": "make easier",
        "grow": "improve",
        "increase": "make clearer",
        "conversions": "responses",
        "revenue": "results",
        "demo": "quick ideas",
        "system": "approach",
        "strategy": "approach",
        "scale": "improve",
        "optimize": "simplify",
        "converting traffic": "easier for visitors",
        "boosting inquiries": "easier to reach you",
        "improving conversions": "clearer next step",
        "increasing revenue": "fewer people leaving",
    }
    t = text
    for k, v in repl.items():
        t = t.replace(k, v).replace(k.capitalize(), v)
    return t

def _short_paragraphs(lines):
    out = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        words = ln.split()
        if len(words) <= 24:
            out.append(" ".join(words))
        else:
            mid = math.ceil(len(words) / 2)
            out.append(" ".join(words[:mid]))
            out.append(" ".join(words[mid:]))
    return out

def _finalize(subject, body, business_name, trade, city, first_name):
    s = _fix_subject(subject, business_name)
    b = _sanitize_language(body)
    lines = [ln.strip() for ln in b.split("\n") if ln.strip()]
    rebuilt = _short_paragraphs(lines)
    intro = f"Hi {first_name if first_name else 'there'},"
    if not rebuilt or not rebuilt[0].lower().startswith("hi "):
        rebuilt.insert(0, intro)
    
    # CTA Injection using new Logic
    cta_text = _get_cta_text(business_name, trade, body) # heuristic: body content implies issue type
    has_good_cta = _has_low_friction_cta("\n".join(rebuilt))
    
    if not has_good_cta:
        rebuilt.append(cta_text)
        # rebuilt.append("No pressure at all.") # Removed to keep it cleaner as per new examples
        rebuilt.append(f"Best regards,\n{config.SENDER_NAME}")
    else:
        # Ensure signature is present
        if config.SENDER_NAME not in rebuilt[-1]:
             rebuilt.append(f"Best regards,\n{config.SENDER_NAME}")
             
    body_out = "\n\n".join(rebuilt)

    if getattr(config, 'ENABLE_SPINTAX', False):
        try:
            import spintax
            s = spintax.spin(s)
            body_out = spintax.spin(body_out)
        except ImportError:
            pass

    if has_banned_phrases(body_out) or has_banned_phrases(s):
        s = f"Quick idea for {business_name}"
        if getattr(config, 'ENABLE_SPINTAX', False):
            try:
                import spintax
                s = spintax.spin(s)
            except ImportError:
                pass

    return s, body_out

def compose_email_from_signals(business_name, first_name, industry, city, signals, country="AU"):
    trade = _detect_service(business_name, industry)
    observation = _compose_observation(signals, country=country)
    tip = _industry_tip(trade)
    subject = f"Quick idea for {business_name}"
    
    cta_text = _get_cta_text(business_name, trade, observation)
    
    parts = [
        f"I came across {business_name} while looking for {trade} services in {city}.",
        f"{observation}.",
        "Often, a very visible call option helps visitors take action instead of leaving.",
        f"{cta_text}",
        f"Best regards,\n{config.SENDER_NAME}",
    ]
    body = "\n\n".join([p for p in parts if p])
    
    # Validate
    valid, reason = _validate_email_content(subject, body, business_name, trade)
    if not valid:
        print(f"Validation failed: {reason}")
    
    return _finalize(subject, body, business_name, trade, city, first_name)

def _finalize_followup(subject, body):
    b = _sanitize_language(body)
    lines = [ln.strip() for ln in b.split("\n") if ln.strip()]
    rebuilt = _short_paragraphs(lines)
    return subject, "\n\n".join(rebuilt)

def generate_followup_1(business_name, first_name, industry, city, secondary_observation=None):
    trade = _detect_service(business_name, industry)
    subject = "Quick follow-up"
    
    lines = [
        f"Hi {business_name} team," if not first_name else f"Hi {first_name},",
        "Just adding one small thought related to my earlier note.",
        "Many visitors come in a hurry, and when the call option isn’t obvious straight away, they often move on faster than expected.",
        "If useful, I’m happy to send a quick idea or two by email.",
        f"Best,\nOlalere Promise Isaac",
    ]
    body = "\n\n".join(lines)
    return _finalize_followup(subject, body)

def generate_followup_2(business_name, first_name, industry, city):
    trade = _detect_service(business_name, industry)
    subject = "One last idea"
    lines = [
        f"Hi {business_name} team," if not first_name else f"Hi {first_name},",
        "I’ll leave it here.",
        "If you’d ever like a couple of quick suggestions by email, feel free to reply anytime.",
        "All the best,\nOlalere Promise Isaac",
    ]
    body = "\n\n".join(lines)
    return _finalize_followup(subject, body)

def classify_reply_intent(reply_text):
    """
    Classifies the reply intent using LLM.
    Categories: YES, LATER, OBJECTION, NO, OTHER
    """
    if not reply_text:
        return {"intent": "OTHER", "confidence": 0.0}
        
    client_groq = Groq(api_key=config.GROQ_API_KEY) if (config.GROQ_API_KEY and Groq is not None) else None
    if not client_groq:
        # Fallback keyword matching
        r = reply_text.lower()
        # Check negatives first
        if "not interested" in r or "unsubscribe" in r or "stop" in r or "remove" in r or "no thanks" in r:
            return {"intent": "NO", "confidence": 0.5}
        if "not now" in r or "later" in r or "busy" in r:
            return {"intent": "LATER", "confidence": 0.5}
        if "already" in r or "price" in r:
            return {"intent": "OBJECTION", "confidence": 0.5}
            
        # Then positives
        if "interested" in r or "call" in r or "yes" in r or "sure" in r:
            return {"intent": "YES", "confidence": 0.5}
            
        return {"intent": "OTHER", "confidence": 0.0}

    prompt = """Classify the reply intent into one category:

- YES: Interested, asks for time, wants details
- LATER: Not now, busy, future timing
- OBJECTION: Price, not needed, already handled
- NO: Clear rejection
- OTHER: Anything else

Return JSON only.

Output Example
{
  "intent": "LATER",
  "confidence": 0.87
}

Reply Text:
""" + reply_text

    try:
        completion = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a precise email classifier. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=50
        )
        content = completion.choices[0].message.content.strip()
        # Extract JSON
        if "{" in content and "}" in content:
            s = content.find("{")
            e = content.rfind("}") + 1
            return json.loads(content[s:e])
        return {"intent": "OTHER", "confidence": 0.0}
    except Exception as e:
        print(f"Classifier Error: {e}")
        return {"intent": "OTHER", "confidence": 0.0}

def generate_followup_3(business_name, first_name, industry, city):
    trade = _detect_service(business_name, industry)
    subject = "One last idea"
    tip = _industry_tip(trade)
    lines = [
        f"Hi {first_name if first_name else 'there'},",
        "Last note from me.",
        f"For {trade}, something as simple as {tip} often makes a difference.",
        "Hope this helps — and wish you a great week.",
        f"{config.SENDER_NAME}",
    ]
    body = "\n\n".join(lines)
    return _finalize(subject, body, business_name, trade, city, first_name)

def qa_tone(subject, body):
    s_bad = has_banned_phrases(subject or "")
    b_bad = has_banned_phrases(body or "")
    marketing_markers = ["schedule", "demo", "optimize", "increase", "grow", "scale"]
    m_hit = any(m in (subject or "").lower() for m in marketing_markers) or any(m in (body or "").lower() for m in marketing_markers)
    return "B" if s_bad or b_bad or m_hit else "A"
def has_banned_phrases(text):
    if not text:
        return False
    banned = [
        "optimize",
        "boost",
        "scale",
        "conversion",
        "strategy",
        "audit",
        "results",
        "grow",
        "increase",
        "automate",
        "we help businesses",
        "i specialize in",
        "on a quick look",
        "it wasn't immediately clear",
        "it wasn’t immediately clear",
        "improve your online presence",
        "reply yes",
        "reply 'yes'",
    ]
    t = (text or "").lower()
    return any(b in t for b in banned)

def generate_subject_options(business_name, industry, city):
    bn = business_name or ""
    c = city or ""
    import sqlite3
    tops = []
    try:
        conn = sqlite3.connect(config.DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT subject FROM training_examples WHERE outcome_type = 'reply' AND subject IS NOT NULL AND subject != '' ORDER BY timestamp DESC LIMIT 3")
        rows = cur.fetchall()
        for r in rows:
            tops.append(r[0])
        conn.close()
    except Exception:
        pass
    base = [
        f"Quick idea for {bn}".strip(),
        "Small website note",
        f"Something I noticed in {c}".strip(),
    ]
    opts = (tops + base)[:3]
    clean = []
    for s in opts:
        s2 = _fix_subject(s, bn)
        if len(s2.split()) > 6:
            s2 = "Quick idea for " + bn
        clean.append(s2)
    return clean[:3]

def get_system_prompt(country="AU", language="EN"):
    base_prompt = """You are a human freelancer sending highly personal cold emails to local service businesses.

Your job:
- Write emails that sound like a personal note, not marketing
- Be calm, helpful, and observant
- Use simple, clear English (unless another language is requested)
- Respect the reader’s time

GLOBAL RULES:
1. Max 110 words
2. Mention EXACTLY one observable website detail
3. No generic praise or marketing language
4. Make only ONE suggestion
5. CTA must be low-friction (reply-based, no call)
6. Subject line must sound like a personal note
7. Never use banned phrases
8. Use industry-specific wording naturally
9. If any rule is violated, regenerate silently
10. HARD RULE: Never ask for a call on first contact.

OBSERVABLE DETAIL RULE:
- Must be something a human could notice in 10 seconds
- Example: “call button isn’t visible on mobile”

TONE RULES:
- Friendly, neutral, professional
- Never hype, never urgency
- Never say “optimize”, “boost”, “scale”, “conversion”

COUNTRY TONE ADAPTATION:
UK/EU:
- Polite, reserved, understated
- Use “might”, “often helps”, “worth considering”

US:
- Friendly, direct, clear
- Slightly conversational

Australia:
- Casual but professional
- Short sentences
- No corporate language

INDUSTRY CONTEXT:
- Plumber / HVAC / Garage Door only
- Emphasize call, booking, emergency when relevant

MENTAL MODEL:
“I noticed something small while browsing — not ‘I analyzed your business.’”

ONE GOLDEN RULE:
If this email could be sent to a competitor without changing the observation, it is a FAIL. It must be specific to *this* website's current state.

CTA RULES (Primary goal: Get a reply, not a meeting):
- No meetings
- No scheduling
- No links
- No pressure
- Must be reply-based

CTA OPTIONS:
1. Async Share (Standard): “If you’d like, I can send over 1–2 quick ideas specific to {{Business Name}} — no call needed.”
2. Yes Reply (Busy): “If helpful, just reply ‘yes’ and I’ll send a couple of quick suggestions.”
3. Visual Example (Design): “I can also send a quick screenshot showing what I mean.”"""

    if language == "DE":
        base_prompt += """

GERMAN EMAIL PROMPT ADDON (🇩🇪)
Write the email in German.
Rules:
- Use “Sie” (formal)
- Do NOT translate idioms literally
- Keep sentences short and clear
- Sound like a local professional, not an agency
- Never sound automated
- CTA: “Falls Sie möchten, kann ich Ihnen 1–2 kurze Ideen in einem 5-minütigen Gespräch teilen.”
"""
    elif language == "FR":
        base_prompt += """

FRENCH EMAIL PROMPT ADDON (🇫🇷)
Write the email in French.
Rules:
- Professional “vous”
- Short paragraphs
- Clear observation
- No sales language
- CTA: “Si cela vous intéresse, je peux partager une ou deux idées rapides lors d’un appel de 5 minutes.”
"""
    else:
        # Default English CTA logic is already in the main prompt/examples implicitly, 
        # but let's make sure it matches the requested format if not explicitly overridden.
        base_prompt += """

CTA FORMAT (English):
“If you’re open to it, I can send over 1–2 quick ideas specific to {{Business Name}} — no call needed.”
"""

    return base_prompt
def get_master_prompt():
    return """You are an AI that writes human, trust-first outreach emails for local service businesses only.

Identity and mindset:
- Behave like a calm professional who noticed one small thing and chose to mention it.
- Goal is only to receive a natural reply, not to sell, explain services, book calls, or persuade.
- If the email feels like marketing, advice, or a pitch → regenerate.

Allowed targets:
- Plumbers, HVAC companies, Roofers, Garage door services, Electricians, Handymen.
- Reject all other industries.

Structure (mandatory order):
1) How you found them (natural browsing context)
2) ONE observable detail from a quick visual scan
3) Why that matters based on customer behavior
4) ONE optional, simple suggestion
5) Reply-based CTA (zero effort)

Observable detail rule:
- Include exactly ONE observable, verifiable detail from the provided observation.
- Use the observation directly in your email.
- Forbidden: SEO, speed, performance, conversions; UX/optimization/structure; any metric, tool, audit, or analysis unless it's the provided observation.

Industry behavior sentence:
- Include ONE short sentence explaining how customers behave in that industry.
- Examples: “Most visitors are usually in a hurry.” “People are often trying to contact someone quickly.” “Visits usually happen when there’s an urgent issue.”
- No stats or numbers.

Suggestion rule:
- Only ONE suggestion; optional, light, non-directive. Use phrasing like:
- “Sometimes just making the call option easier to spot helps.”
- “Often a simple ‘Call / Book’ section makes it clearer.”
- Never say “you should”.

CTA rule:
- Never ask for calls, meetings, calendars, audits, screenshots, links, attachments.
- Allowed CTAs: “If helpful, just reply ‘yes’ and I’ll send a couple of quick ideas.” or “Happy to share 1–2 thoughts by email.” or “Let me know if you’d like me to send a quick suggestion.”

Banned words:
- If any appear, regenerate: optimize, boost, scale, conversion, strategy, audit, results, grow, increase, automate, we help businesses, I specialize in.

Subject line rules:
- Must feel like a personal note. Allowed patterns:
- “Quick note about {{Business Name}}”
- “Small thing I noticed on {{Business Name}}”
- “One observation about {{Business Name}}”
- No promises, benefits, or emojis.

Length and tone:
- 90–120 words total, plain language, short paragraphs, calm, respectful, human.

Country and language tone switching:
- US: Friendly, natural; UK/EU: Polite, reserved; Australia: Casual-professional; Germany: Formal (Sie), direct, neutral; France: Polite, professional, warm.
- Never use idioms outside US/AU.

Micro-personalization check:
- Reject output if only personalization is business name, no location or service context, or observation is generic.

Quality scoring:
- Observable detail (20), Industry behavior (15), One suggestion (10), No banned words (20), Reply-based CTA (15), Natural tone (10), Correct length (10).
- Regenerate if score < 85 or any hard rule fails.

Follow-ups:
- Max 2; first adds one gentle thought; second closes politely; never chase or pressure.

Reply intent handling:
- YES: send value email; LATER: acknowledge and pause; NO: thank and stop; QUESTION: answer briefly, no pitch.

Final self-check:
- If competitor-ready, marketing tone, effort-required, or multiple issues → regenerate.

Core principle:
- If the prospect does nothing, the email still succeeded. Trust over tactics."""
def score_master_email(subject, body):
    s = 0
    if has_banned_phrases(subject) or has_banned_phrases(body):
        return 0
    bl = len((body or "").split())
    if 90 <= bl <= 120:
        s += 10
    if any(k in (body or "").lower() for k in ["most visitors","often trying to contact","urgent issue"]):
        s += 15
    if any(k in (body or "").lower() for k in ["call option","call / book","book section","booking","call button"]):
        s += 10
    if _has_low_friction_cta(body or ""):
        s += 15
    s += 20
    s += 10
    s += 20
    return s
def generate_email_master(business_name, industry, city, observation, country="US"):
    subj = f"Small thing I noticed on {business_name}"
    body = ""
    client = Groq(api_key=config.GROQ_API_KEY) if (config.GROQ_API_KEY and Groq is not None) else None
    if client:
        sys = get_master_prompt()
        up = {
            "business_name": business_name,
            "industry": industry,
            "city": city,
            "country": country,
            "observation": observation
        }
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"system","content":sys},{"role":"user","content":json.dumps(up)}],
                temperature=0.3,
                max_tokens=400
            )
            content = completion.choices[0].message.content.strip()
            if "\n" in content:
                lines = [l for l in content.split("\n") if l.strip()]
                s_line = lines[0]
                if len(s_line) < 90 and "@" not in s_line and "about" in s_line.lower():
                    subj = s_line
                    body = "\n\n".join(lines[1:]) if len(lines) > 1 else "\n".join(lines)
                else:
                    body = content
            else:
                body = content
        except Exception:
            pass
    if not body:
        obs = observation or "the call option wasn’t obvious on first view"
        parts = [
            f"I came across {business_name} while looking at {industry} services in {city}.",
            f"One thing I noticed was {obs}.",
            "People are often trying to contact someone quickly.",
            "Sometimes just making the call option easier to spot helps.",
            _get_cta_text(business_name, industry, obs),
            f"Best regards,\n{config.SENDER_NAME}"
        ]
        body = "\n\n".join(parts)
    score = score_master_email(subj, body)
    if score < 85:
        parts = [
            f"I was browsing local {industry} services in {city} and found {business_name}.",
            f"One thing that stood out was {observation or 'the booking step still takes an extra beat to spot'}.",
            "Most visitors are usually in a hurry.",
            "Often a simple ‘Call / Book’ section makes it clearer.",
            _get_cta_text(business_name, industry, observation or "call / book"),
            f"Best regards,\n{config.SENDER_NAME}"
        ]
        body = "\n\n".join(parts)
        subj = f"Quick note about {business_name}"
    return subj, body

def get_user_prompt(input_json):
    return "\n".join([
        "Write a personalized cold email using the provided JSON rules and input data.",
        "Requirements:",
        "- Follow the exact email structure",
        "- Apply industry-specific logic",
        "- Avoid all banned words",
        "- Use neutral, friendly language",
        "- Sound like a real person",
        "Input Data:",
        json.dumps(input_json),
        "Output:",
        "A single cold email.",
    ])

def get_subject_prompt(business_name, industry, city):
    return "\n".join([
        "Generate 3 subject line options.",
        "Rules:",
        "- Max 6 words",
        "- No sales language",
        "- No hype",
        "- No emojis",
        "- Must sound human",
        "Context:",
        f"{business_name}, {industry}, {city}",
    ])

def get_followup1_prompt(input_json):
    return "\n".join([
        "Write a short follow-up to a previous cold email.",
        "Rules:",
        "- Reference the previous message lightly",
        "- Add ONE new observation",
        "- No selling",
        "- Max 60 words",
        "- Friendly, calm tone",
        "Context:",
        json.dumps(input_json),
    ])

def get_followup2_prompt(business_name):
    return "\n".join([
        "Write a polite follow-up asking whether to close the loop.",
        "Rules:",
        "- No pressure",
        "- Respectful tone",
        "- Max 40 words",
        "- Must invite a reply",
        "Context:",
        business_name or "",
    ])

def get_self_qa_prompt():
    return "\n".join([
        "Does this email sound like:",
        "A) a helpful person who noticed something",
        "B) a marketer trying to sell",
        "If B, rewrite the email to sound like A.",
    ])

def compose_email_from_json(data):
    website = data.get("website") or {}
    reviews = data.get("reviews") or {}
    signals = {
        "website_exists": bool(website.get("exists", True)),
        "website_mobile_friendly": bool(website.get("mobile_friendly", True)),
        "cta_visibility": website.get("cta_visibility") or "unclear",
        "contact_method": website.get("contact_method") or "unclear",
        "reviews_present": bool(reviews.get("present", False)),
        "google_rating": reviews.get("google_rating"),
    }
    return compose_email_from_signals(
        data.get("business_name"),
        data.get("first_name"),
        data.get("industry"),
        data.get("city"),
        signals,
    )

def generate_email_content(business_name, trade, city, strategy="audit", audit_issues=None, description=None, reviews=None, first_name=None, country="AU"):
    trade = _detect_service(business_name, trade)
    country_config = _get_country_config(country)
    
    if (not config.GROQ_API_KEY or Groq is None) and (not config.OPENAI_API_KEY or OpenAI is None):
        # Use Master Spintax Template as robust fallback
        return generate_spintax_email(business_name, city, trade, first_name)

    client_groq = Groq(api_key=config.GROQ_API_KEY) if (config.GROQ_API_KEY and Groq is not None) else None
    
    # 1. Prepare Context
    specific_issue, quick_fix = _choose_problem_context(audit_issues or [])
    
    review_context = ""
    if reviews and len(reviews) > 0:
        review_context = f"I came across {business_name} while looking at {trade} businesses in {city}."
    else:
        review_context = f"I came across {business_name} while looking for {trade} services in {city}."

    # 2. Construct the Advanced Prompt
    system_prompt = get_system_prompt(country)

    user_prompt = f"""
    Generate a cold email for:
    - Business Name: {business_name}
    - Trade: {trade}
    - City: {city}
    - First Name: {first_name if first_name else "there"}
    - Specific Issue: {specific_issue}
    - Quick Fix: {quick_fix}
    - Hook Context: {review_context}
    
    Output strictly the Subject and Body. 
    Start the response with "Subject:".
    Include the greeting "Hi {first_name if first_name else 'there'}," at the start of the body.
    """

    for attempt in range(2): # Try up to 2 times
        try:
            if client_groq:
                completion = client_groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt + (f"\n\nPrevious attempt failed: {validation_error}. Please fix." if attempt > 0 else "")}
                    ],
                    temperature=0.8, 
                    max_tokens=400
                )
                content = completion.choices[0].message.content.strip()
                
                subject = _get_fallback_subject(business_name)
                body = ""

                if "Subject:" in content:
                    parts = content.split("Subject:", 1)[1].split("\n", 1)
                    subject = parts[0].strip()
                    body = parts[1].strip() if len(parts) > 1 else ""
                else:
                    body = content

                body = _enforce_rules(subject, body, business_name, trade, city, first_name)
                subject = _fix_subject(subject, business_name)
                
                # Double check with _finalize
                subject, body = _finalize(subject, body, business_name, trade, city, first_name)
                
                # Validation
                valid, validation_error = _validate_email_content(subject, body, business_name, trade)
                if valid:
                    return subject, body
                else:
                    print(f"Validation failed (Attempt {attempt+1}): {validation_error}")
                    continue

        except Exception as e:
            print(f"LLM Generation Error: {e}")
            break # Fallback to deterministic
            
    # Fallback if LLM fails or validation fails repeatedly
    specific_issue, quick_fix = _choose_problem_context(audit_issues or [])
    buffer = country_config.get("buffer", "One thing I noticed is")
    subject = f"Quick idea for {business_name}"
    cta_text = _get_cta_text(business_name, trade, specific_issue)
    
    body = "\n".join([
        f"Hi {first_name or 'there'},",
        "",
        f"I came across {business_name} while looking for {trade} services in {city}.",
        f"{buffer} {specific_issue}.",
        "When that happens, some visitors leave without reaching out — not because of the service, but because they’re unsure what to do next.",
        f"Often, something simple like {quick_fix.split(',')[0]} can help.",
        f"{cta_text}",
        f"Best regards,\n{config.SENDER_NAME}",
    ])
    return subject, _enforce_rules(subject, body, business_name, trade, city, first_name)

def has_banned_phrases(text):
    banned = [
        "guaranteed",
        "free $$$",
        "act now",
        "risk-free",
        "winner",
        "urgent",
        "limited time",
        "money back",
        "cash bonus",
        "boost",
        "grow",
        "increase",
        "scale",
        "optimize",
        "converting traffic",
        "boosting inquiries",
        "improving conversions",
        "increasing revenue",
        "custom demo",
        "schedule",
        # New banned phrases
        "improving",
        "optimizing",
        "enhancing",
        "visitor experience",
        "a lot to offer",
        "great website",
        "strong presence",
        "on a quick look",
        "it wasn't immediately clear",
        "it wasn’t immediately clear",
        "improve your online presence",
        "reply yes",
        "reply 'yes'",
    ]
    if not text:
        return False
    t = text.lower()
    return any(p in t for p in banned)

def score_email(subject, body):
    try:
        s_len = len(subject or "")
        paras = [p.strip() for p in (body or "").split("\n") if p.strip() != ""]
        b_len = len(body or "")
        score = 0
        if 8 <= s_len <= 80 and not has_banned_phrases(subject):
            score += 2
        if 60 <= b_len <= 600 and all(len(p.split()) <= 24 for p in paras):
            score += 2
        if not has_banned_phrases(body):
            score += 2
        return max(1, min(5, score // 2 + 2))
    except Exception:
        return 3

def _fix_subject(subject, business_name):
    s = (subject or "").strip()
    banned_starts = ["improving", "optimizing", "enhancing", "visitor experience"]
    if any(s.lower().startswith(b) for b in banned_starts) or has_banned_phrases(s) or len(s) < 6:
        return f"Quick idea for {business_name}"
    return s

def _enforce_rules(subject, body, business_name, trade, city, first_name):
    s = _fix_subject(subject, business_name)
    text = (body or "").strip()
    text = text.replace("converting traffic", "easier for visitors").replace("boosting inquiries", "easier to reach you").replace("improving conversions", "clearer next step").replace("increasing revenue", "fewer people leaving")
    lines = [ln.strip() for ln in text.split("\n") if ln.strip() != ""]
    rebuilt = []
    for ln in lines:
        words = ln.split()
        if len(words) > 24:
            mid = len(words) // 2
            rebuilt.append(" ".join(words[:mid]))
            rebuilt.append(" ".join(words[mid:]))
        else:
            rebuilt.append(ln)
    intro = f"Hi {first_name if first_name else 'there'},"
    if not rebuilt or not rebuilt[0].lower().startswith("hi "):
        rebuilt.insert(0, intro)
    
    # CTA Injection if missing (Safe Fallback)
    # Using a generic low-friction CTA if the body doesn't seem to have one
    has_good_cta = _has_low_friction_cta("\n".join(rebuilt))
    
    if not has_good_cta:
        rebuilt.append(_get_cta_text(business_name, trade, "\n".join(rebuilt)))
        rebuilt.append(f"Best regards,\n{config.SENDER_NAME}")
    
    return "\n\n".join(rebuilt)

# ==========================================
# NEW FEATURES: Snapshot, CRM, QA Dashboard
# ==========================================

def _generate_observation_from_snapshot(snapshot):
    """
    Generates a single specific observation from a website snapshot.
    Logic: First Match Only (Priority Order).
    
    Snapshot Schema (Expected):
    {
        "mobile_view_ok": bool,
        "call_button_visible": bool,
        "contact_form_visible": bool,
        "last_blog_date": str (YYYY-MM-DD) or None,
        "hero_text": str,
        "nav_links": list
    }
    """
    if not snapshot:
        return "the first contact path was harder to spot than it should be"

    # 1. Mobile View = False
    if snapshot.get("mobile_view_ok") is False:
        return "the mobile view didn't feel fully optimized for quick booking"
    
    # 2. Call Button Visible = False
    if snapshot.get("call_button_visible") is False:
        return "the tap-to-call button wasn't easy to find on a first glance"

    # 3. Form Visible = False
    if snapshot.get("contact_form_visible") is False:
        return "the contact form took a few clicks to find"

    # 4. Fallback
    return "the homepage does not make the first next step obvious enough"

def validate_crm_contact(contact):
    """
    Validates a contact against the CRM schema.
    Required: email, business_name, first_name.
    """
    required = ["email", "business_name", "first_name"]
    missing = [f for f in required if not contact.get(f)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    
    if "@" not in contact.get("email", ""):
        return False, "Invalid email format"
        
    return True, "Valid"

def check_crm_duplicate(email):
    """
    Placeholder: Checks if email already exists in CRM (HubSpot/Pipedrive/Airtable).
    Returns True if duplicate, False if safe to send.
    """
    # In a real implementation, this would query the CRM API.
    # For now, we assume no duplicate (or implement a simple local check if needed).
    return False

def update_crm_on_reply(email, reply_intent):
    """
    Placeholder: Updates the contact status in CRM based on reply intent.
    """
    print(f"[CRM SYNC] Updating {email} status to: {reply_intent}")
    return True

def generate_qa_dashboard_metrics(email_logs):
    """
    Generates QA metrics from a list of email logs.
    Logs Schema: [{ "status": "sent/replied/bounced", "reply_intent": "YES/NO...", "language": "EN/DE/FR", "industry": "..." }]
    """
    total = len(email_logs)
    if total == 0:
        return {"total_sent": 0, "reply_rate": "0%"}
        
    replies = [l for l in email_logs if l.get("status") == "replied"]
    reply_rate = (len(replies) / total) * 100
    
    positive_replies = [r for r in replies if r.get("reply_intent") == "YES"]
    positive_rate = (len(positive_replies) / len(replies) * 100) if replies else 0
    
    # Breakdown by Language
    lang_stats = {}
    for l in ["EN", "DE", "FR"]:
        sent_l = [x for x in email_logs if x.get("language") == l]
        replies_l = [x for x in sent_l if x.get("status") == "replied"]
        if sent_l:
            lang_stats[l] = f"{(len(replies_l) / len(sent_l) * 100):.1f}% ({len(replies_l)}/{len(sent_l)})"
            
    return {
        "total_sent": total,
        "reply_rate": f"{reply_rate:.1f}%",
        "positive_reply_rate": f"{positive_rate:.1f}%",
        "language_breakdown": lang_stats
    }


ELITE_PERSONAS = {
    "Revenue Hacker": "Focus on revenue leaks and missed conversions.",
    "SEO Sniper": "Focus on rankings, reviews, and competitor gaps.",
    "CX Fixer": "Focus on user friction, trust issues, and unclear next steps.",
    "Automation Operator": "Focus on time waste and manual follow-up friction.",
    "Authority Builder": "Focus on branding, trust, and premium positioning.",
    "Competitor Spy": "Focus on competitor advantage gaps and positioning.",
}

ELITE_GENERIC_PHRASES = [
    "on a quick look",
    "it wasn't immediately clear",
    "it wasn’t immediately clear",
    "i help businesses",
    "i help businesses grow",
    "help businesses grow",
    "improve your online presence",
    "take your business to the next level",
    "unlock more leads",
    "grow your business",
    "increase conversions",
    "scale your business",
]

ELITE_SPECIFICITY_KEYWORDS = [
    "mobile",
    "call",
    "book",
    "booking",
    "contact",
    "form",
    "footer",
    "phone",
    "speed",
    "slow",
    "ssl",
    "https",
    "reviews",
    "rating",
    "wix",
    "wordpress",
    "shopify",
    "google",
    "maps",
]

ELITE_HOOK_TYPES = [
    "question",
    "contrarian",
    "data_observation",
    "competitor_comparison",
    "mistake_callout",
]

ELITE_PERSONA_REQUIRED_TOKENS = {
    "Revenue Hacker": ["revenue", "calls", "jobs", "quotes", "quote", "booked", "enquiries", "inquiries", "lost"],
    "SEO Sniper": ["google", "maps", "reviews", "review", "rating", "search", "rank"],
    "CX Fixer": ["call", "contact", "book", "booking", "form", "phone", "button", "friction"],
    "Automation Operator": ["manual", "follow-up", "follow up", "admin", "back-and-forth", "wasted", "time"],
    "Authority Builder": ["trust", "credibility", "premium", "brand", "proof", "specialist", "authority"],
    "Competitor Spy": ["competitor", "compared", "versus", "gap", "alternative", "local market"],
}

ELITE_WEAK_CTA_PHRASES = [
    "reply yes",
    "reply 'yes'",
]

ELITE_LOW_FRICTION_CTA_MARKERS = [
    "if helpful, i can send",
    "if useful, i can send",
    "if it helps, i can",
    "happy to send",
    "worth pointing out",
    "can send the two",
    "can send over two",
    "can point out the two",
    "marked-up screenshot",
    "quick screenshot",
    "share a quick screenshot",
    "quick example",
    "quick notes",
    "first two fixes",
    "no call needed",
    "via email",
]

ELITE_GENERIC_OBSERVATION_MARKERS = [
    "next step",
    "online presence",
    "not obvious",
    "wasn't obvious",
    "visitor experience",
    "could be improved",
    "room for improvement",
    "needs a modern touch",
]


def _trim_text(value, limit=280):
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _stable_choice(options, *parts):
    if not options:
        return ""
    basis = "|".join(str(part or "") for part in parts)
    index = sum(ord(char) for char in basis) % len(options)
    return options[index]


def _has_low_friction_cta(text):
    lower = (text or "").lower()
    if any(
        phrase in lower
        for phrase in ["quick call", "schedule", "meeting", "zoom", "demo", "book a time", "hop on a call"]
    ):
        return False
    return any(marker in lower for marker in ELITE_LOW_FRICTION_CTA_MARKERS)


def _looks_generic_observation(text):
    lower = (text or "").lower().strip()
    if len(lower.split()) < 4:
        return True
    return any(marker in lower for marker in ELITE_GENERIC_OBSERVATION_MARKERS)


def _observation_tokens(text):
    stopwords = {
        "their", "there", "about", "could", "would", "should", "while", "which",
        "because", "after", "before", "under", "with", "from", "that", "this",
        "have", "your", "site", "website", "homepage", "business", "people",
        "first", "thing", "looked", "look", "noticed",
    }
    return [
        token for token in re.findall(r"[a-z0-9][a-z0-9/&+-]{3,}", (text or "").lower())
        if token not in stopwords
    ]


def _observation_is_used(observation, *texts):
    combined = " ".join(texts).lower()
    tokens = _observation_tokens(observation)
    return any(token in combined for token in tokens[:4])


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = [part.strip() for part in re.split(r"[;\n]+", value) if part.strip()]
        return parts or [value.strip()]
    return [str(value).strip()]


def _infer_country_code(location):
    text = (location or "").lower()
    if "uk" in text or "united kingdom" in text:
        return "UK"
    if "australia" in text:
        return "AU"
    if "germany" in text or "france" in text or "europe" in text or "eu" in text:
        return "EU"
    if "usa" in text or "united states" in text or "canada" in text:
        return "US"
    if re.search(r",\s*[A-Z]{2}(?:,|$)", location or ""):
        return "US"
    return "US"


def _build_elite_prompt_payload(lead_data):
    website_signals = lead_data.get("website_signals") or {}
    competitors = []
    for item in (lead_data.get("competitors") or [])[:3]:
        if isinstance(item, dict):
            competitors.append({
                "business_name": _trim_text(item.get("business_name"), 80),
                "website": _trim_text(item.get("website"), 120),
                "rating": item.get("rating"),
            })
        else:
            competitors.append({"business_name": _trim_text(item, 80)})

    payload = {
        "business_name": lead_data.get("business_name"),
        "first_name": lead_data.get("first_name") or "there",
        "industry": lead_data.get("industry"),
        "city": lead_data.get("city"),
        "website": lead_data.get("website"),
        "email": lead_data.get("email"),
        "rating": lead_data.get("rating"),
        "review_count": lead_data.get("review_count"),
        "pagespeed_score": lead_data.get("pagespeed_score"),
        "description": _trim_text(lead_data.get("description"), 320),
        "audit_issues": _as_list(lead_data.get("audit_issues"))[:6],
        "website_signals": {
            "website_exists": bool(lead_data.get("website")),
            "website_mobile_friendly": website_signals.get("website_mobile_friendly"),
            "cta_visibility": website_signals.get("cta_visibility"),
            "contact_method": website_signals.get("contact_method"),
            "tech": list(website_signals.get("tech", [])[:5]) if isinstance(website_signals.get("tech"), list) else [],
            "pagespeed_score": lead_data.get("pagespeed_score"),
            "page_title": _trim_text(website_signals.get("page_title"), 120),
            "meta_description": _trim_text(website_signals.get("meta_description"), 200),
            "headline": _trim_text(website_signals.get("headline"), 140),
            "services": [_trim_text(item, 80) for item in (website_signals.get("services") or [])[:6]],
            "cta_labels": [_trim_text(item, 60) for item in (website_signals.get("cta_labels") or [])[:5]],
            "trust_markers": [_trim_text(item, 40) for item in (website_signals.get("trust_markers") or [])[:5]],
            "homepage_summary": _trim_text(website_signals.get("homepage_summary"), 320),
        },
        "reviews": [_trim_text(review, 180) for review in (lead_data.get("reviews") or [])[:3]],
        "competitors": competitors,
    }
    payload["evidence"] = _build_elite_evidence_bank(payload)
    payload["evidence_categories"] = _extract_evidence_categories(payload)
    return payload


def _build_elite_evidence_bank(payload):
    evidence = []
    business_name = payload.get("business_name") or "This business"
    rating = payload.get("rating")
    review_count = payload.get("review_count")
    website_signals = payload.get("website_signals") or {}

    if rating and review_count:
        evidence.append(f"{business_name} is sitting at {rating} stars from {review_count} Google reviews")
    elif review_count:
        evidence.append(f"{business_name} has {review_count} customer reviews on Google")

    for review in (payload.get("reviews") or [])[:2]:
        evidence.append(f"Review snippet: {review.rstrip('.')}")

    if payload.get("description"):
        evidence.append(f"Directory description: {payload['description'].rstrip('.')}")
    if website_signals.get("headline"):
        evidence.append(f"Homepage headline: {website_signals['headline'].rstrip('.')}")
    if website_signals.get("page_title"):
        evidence.append(f"Page title: {website_signals['page_title'].rstrip('.')}")
    if website_signals.get("meta_description"):
        evidence.append(f"Meta description: {website_signals['meta_description'].rstrip('.')}")
    if website_signals.get("services"):
        evidence.append(
            "Services called out on the site: "
            + ", ".join(item.rstrip(".") for item in website_signals["services"][:4])
        )
    if website_signals.get("cta_labels"):
        evidence.append(
            "Visible call-to-action labels: "
            + ", ".join(item.rstrip(".") for item in website_signals["cta_labels"][:4])
        )
    if website_signals.get("trust_markers"):
        evidence.append(
            "Trust markers shown on the site: "
            + ", ".join(item.rstrip(".") for item in website_signals["trust_markers"][:4])
        )
    if website_signals.get("homepage_summary"):
        evidence.append(f"Homepage copy snapshot: {website_signals['homepage_summary'].rstrip('.')}")
    if website_signals.get("contact_method") == "form":
        evidence.append("The site appears to rely on a form as the main contact path")
    elif website_signals.get("contact_method") == "phone":
        evidence.append("The site gives people a direct phone path from the homepage")
    if website_signals.get("website_mobile_friendly") is False:
        evidence.append("The homepage is missing a viewport tag, so mobile rendering may be rough")
    if website_signals.get("cta_visibility") == "unclear":
        evidence.append("The homepage does not surface one dominant next step above the fold")

    pagespeed_score = payload.get("pagespeed_score")
    if pagespeed_score is not None:
        try:
            evidence.append(f"Google PageSpeed score: {int(float(pagespeed_score) * 100)}/100")
        except Exception:
            pass

    for issue in (payload.get("audit_issues") or [])[:3]:
        evidence.append(f"Audit finding: {str(issue).rstrip('.')}")

    for competitor in (payload.get("competitors") or [])[:2]:
        competitor_name = competitor.get("business_name")
        if not competitor_name:
            continue
        rating_text = f" at {competitor.get('rating')} stars" if competitor.get("rating") else ""
        evidence.append(f"Competitor reference: {competitor_name}{rating_text}")

    deduped = []
    seen = set()
    for item in evidence:
        cleaned = _trim_text(item, 220).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
        if len(deduped) >= 10:
            break
    return deduped


def _extract_evidence_categories(prompt_payload):
    categories = set()
    website_signals = prompt_payload.get("website_signals") or {}

    if prompt_payload.get("competitors"):
        categories.add("competitor_gap")

    if prompt_payload.get("rating") or prompt_payload.get("review_count") or prompt_payload.get("reviews"):
        categories.add("review_problem")

    if website_signals.get("contact_method") == "form" or website_signals.get("cta_visibility") == "unclear" or website_signals.get("website_mobile_friendly") is False or prompt_payload.get("audit_issues"):
        categories.add("ux_friction")

    if prompt_payload.get("description") or website_signals.get("headline") or website_signals.get("services"):
        categories.add("positioning")

    return list(categories)


def _normalize_hook_type_label(hook_type):
    if not hook_type:
        return None
    normalized = (hook_type or "").strip().lower()
    if normalized == "data_observation":
        return "observation"
    if normalized == "mistake_callout":
        return "contrarian"
    if normalized == "competitor_comparison":
        return "competitor"
    return normalized


def _last_successful_hook_type(prompt_payload):
    outcomes = prompt_payload.get("past_outcomes") or []
    success_counts = {}
    for event in outcomes:
        if event.get("type") not in ("reply", "appointment_booked", "sale_closed"):
            continue
        meta = event.get("meta") or {}
        hook = _normalize_hook_type_label(meta.get("hook_type"))
        if hook:
            success_counts[hook] = success_counts.get(hook, 0) + 1
    if not success_counts:
        return None
    return max(success_counts, key=lambda k: success_counts[k])


def _last_sent_hook_type(prompt_payload):
    outcomes = prompt_payload.get("past_outcomes") or []
    for event in outcomes:
        if event.get("type") in ("email_generated", "sent", "email_send_attempt"):
            meta = event.get("meta") or {}
            hook = _normalize_hook_type_label(meta.get("hook_type"))
            if hook:
                return hook
    return None


def _primary_evidence_category(prompt_payload):
    categories = _extract_evidence_categories(prompt_payload)
    if "competitor_gap" in categories:
        return "competitor_gap"
    if "ux_friction" in categories:
        return "ux_friction"
    if "review_problem" in categories:
        return "review_problem"
    if "positioning" in categories:
        return "positioning"
    return None


def _preferred_hook_type(prompt_payload, persona):
    if persona == "Competitor Spy" and prompt_payload.get("competitors"):
        return "competitor_comparison"

    successful_hook = _last_successful_hook_type(prompt_payload)
    if successful_hook:
        return successful_hook

    category = _primary_evidence_category(prompt_payload)
    if category == "competitor_gap":
        return "competitor_comparison"
    if category == "ux_friction":
        return "question"
    if category == "review_problem":
        return "data_observation"

    website_signals = prompt_payload.get("website_signals") or {}
    if website_signals.get("headline") or website_signals.get("services"):
        return "question"

    if any(event.get("type") == "opened" for event in (prompt_payload.get("past_outcomes") or [])) and not any(event.get("type") in ("reply", "appointment_booked", "sale_closed") for event in (prompt_payload.get("past_outcomes") or [])):
        last_hook = _last_sent_hook_type(prompt_payload)
        if last_hook and last_hook in ELITE_HOOK_TYPES:
            alternatives = [hook for hook in ELITE_HOOK_TYPES if hook != last_hook]
            if alternatives:
                return alternatives[0]

    return _stable_choice(ELITE_HOOK_TYPES, prompt_payload.get("business_name"), prompt_payload.get("city"), persona)


def _elite_specificity_tokens(lead_data):
    payload = _build_elite_prompt_payload(lead_data)
    context_text = json.dumps(payload, ensure_ascii=True).lower()
    website_signals = payload.get("website_signals") or {}
    markers = [token for token in ELITE_SPECIFICITY_KEYWORDS if token in context_text]

    if payload.get("rating") is not None:
        markers.append(str(payload.get("rating")).lower())
    if payload.get("review_count"):
        markers.append(str(payload.get("review_count")).lower())

    for item in (
        website_signals.get("services", [])[:4]
        + website_signals.get("cta_labels", [])[:4]
        + website_signals.get("trust_markers", [])[:4]
    ):
        lowered = str(item).lower().strip()
        if lowered:
            markers.append(lowered)
            markers.extend(_observation_tokens(lowered)[:2])

    if website_signals.get("headline"):
        markers.extend(_observation_tokens(website_signals["headline"])[:4])

    for competitor in (payload.get("competitors") or [])[:2]:
        competitor_name = (competitor.get("business_name") or "").lower().strip()
        if competitor_name:
            markers.append(competitor_name)

    deduped = []
    seen = set()
    for marker in markers:
        cleaned = marker.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        deduped.append(cleaned)
        if len(deduped) >= 24:
            break
    return deduped


def _persona_angle_sentence(persona, trade):
    if persona == "Revenue Hacker":
        return f"For {trade}, the people ready to call or request a quote usually decide fast, so hesitation on the page tends to cost the better jobs first."
    if persona == "SEO Sniper":
        return "When someone clicks through after seeing strong reviews, the site has to confirm that trust quickly."
    if persona == "CX Fixer":
        return "People deciding in a hurry usually drop when the first action takes an extra step."
    if persona == "Automation Operator":
        return "When the first contact path leans on forms or back-and-forth, the best enquiries turn into admin."
    if persona == "Authority Builder":
        return "The reputation is already there, but the site should reinforce that specialist signal more clearly."
    if persona == "Competitor Spy":
        return "In local service markets, the business that makes the right offer easiest to spot usually takes the first call."
    return "A small fix to the first decision step can change how many good enquiries actually come through."


def _fallback_observations(lead_data):
    prompt_payload = _build_elite_prompt_payload(lead_data)
    observations = []
    for item in prompt_payload.get("evidence") or []:
        cleaned = _trim_text(str(item).rstrip("."), 180)
        if cleaned and not _looks_generic_observation(cleaned):
            observations.append(cleaned)
        if len(observations) >= 3:
            break
    return observations


def _compose_fallback_hook(hook_type, business_name, observations, competitors=None):
    primary = (observations[0] if observations else "there is a concrete website detail worth fixing").rstrip(".")
    competitor_name = None
    for competitor in competitors or []:
        competitor_name = competitor.get("business_name")
        if competitor_name:
            break

    if hook_type == "question":
        return f"Quick question: have you already looked at how this is coming across on the site for {business_name}: {primary}?"
    if hook_type == "contrarian":
        return f"The issue probably is not the service itself. It is that {primary.lower()}."
    if hook_type == "competitor_comparison" and competitor_name:
        return f"I noticed {competitor_name} is more explicit about one thing locally, while {business_name} is quieter about it: {primary}."
    if hook_type == "mistake_callout":
        return f"The miss is not the work quality. It is that {primary.lower()}."
    return f"One thing that jumped out was {primary}."


def _default_elite_persona(lead_data):
    context_text = json.dumps(_build_elite_prompt_payload(lead_data), ensure_ascii=True).lower()
    if any(token in context_text for token in ["review", "rating", "google", "maps", "seo"]):
        return "SEO Sniper"
    if len(lead_data.get("competitors") or []) >= 2:
        return "Competitor Spy"
    if any(token in context_text for token in ["mobile", "call", "book", "contact", "form", "footer"]):
        return "CX Fixer"
    if any(token in context_text for token in ["manual", "follow", "automation"]):
        return "Automation Operator"
    if any(token in context_text for token in ["licensed", "insured", "certified", "premium", "authority"]):
        return "Authority Builder"
    if not lead_data.get("website"):
        return "Authority Builder"
    return "Revenue Hacker"


def _fallback_insight(lead_data):
    observations = _fallback_observations(lead_data)
    if observations:
        return observations[0]

    issues = _as_list(lead_data.get("audit_issues"))
    if issues:
        return issues[0]

    signals = lead_data.get("website_signals") or {}
    if signals.get("website_mobile_friendly") is False:
        return "the mobile experience may make it harder for people to reach you quickly"
    if signals.get("cta_visibility") == "unclear":
        return "the next step to contact you is not obvious on first view"
    if signals.get("contact_method") == "form":
        return "the contact path leans on forms, which can slow down urgent enquiries"
    if not lead_data.get("website"):
        return "there is no clear website presence supporting the reputation you already have locally"
    return "the first contact step is not as clear as it could be for someone ready to reach out"


def _build_fallback_elite_result(lead_data, country=None):
    business_name = lead_data.get("business_name") or "your business"
    first_name = lead_data.get("first_name") or "there"
    trade = _detect_service(business_name, lead_data.get("industry"))
    city = lead_data.get("city") or "your area"
    prompt_payload = _build_elite_prompt_payload(lead_data)
    persona = _default_elite_persona(lead_data)
    observations = _fallback_observations(lead_data)
    insight = (observations[0] if observations else _fallback_insight(lead_data)).rstrip(".")
    hook_type = _preferred_hook_type(prompt_payload, persona)
    strategy_text = (
        f"Lead with a {persona.lower()} angle, anchor the note in scraped evidence, "
        "and keep the CTA low-friction."
    )
    cta_text = _get_cta_text(business_name, trade, f"{persona} {insight}")
    support_line = ""
    if len(observations) > 1:
        support_line = f"I also noticed {observations[1].rstrip('.').lower()}, which adds a bit of friction right where intent is highest."

    body = "\n\n".join([
        f"Hi {first_name},",
        f"I came across {business_name} while looking at {trade} businesses in {city}.",
        _compose_fallback_hook(hook_type, business_name, observations, prompt_payload.get("competitors")),
        support_line,
        _persona_angle_sentence(persona, trade),
        cta_text,
        f"Best regards,\n{config.SENDER_NAME}",
    ])
    body = "\n\n".join(part for part in body.split("\n\n") if part)
    subject, body = _finalize(
        f"Quick note about {business_name}",
        body,
        business_name,
        trade,
        city,
        first_name,
    )
    return {
        "persona": persona,
        "hook_type": hook_type,
        "observations": observations[:3],
        "strategy": strategy_text,
        "insight": insight,
        "subject": subject,
        "email": body,
        "provider": "fallback",
    }


def _extract_json_payload(content):
    if not content:
        raise ValueError("Empty LLM response")

    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("LLM did not return JSON")

    return json.loads(text[start : end + 1])


def _run_elite_llm(system_prompt, user_prompt, temperature=0.8, max_tokens=1100):
    last_error = None

    if config.GROQ_API_KEY and Groq is not None:
        try:
            client = Groq(api_key=config.GROQ_API_KEY)
            completion = client.chat.completions.create(
                model=getattr(config, "GROQ_MODEL", "llama-3.3-70b-versatile"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content.strip(), "groq"
        except Exception as exc:
            last_error = exc
            if not (config.OPENAI_API_KEY and OpenAI is not None):
                raise

    if config.OPENAI_API_KEY and OpenAI is not None:
        try:
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            completion = client.chat.completions.create(
                model=getattr(config, "OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content.strip(), "openai"
        except Exception as exc:
            last_error = exc

    if last_error:
        raise RuntimeError(f"LLM provider failed: {last_error}")

    raise RuntimeError("No LLM provider configured")

def _elite_quality_issues(result, lead_data):
    business_name = (lead_data.get("business_name") or "").strip()
    subject = _fix_subject(result.get("subject") or "", business_name)
    email = (result.get("email") or "").strip()
    persona = (result.get("persona") or "").strip()
    hook_type = (result.get("hook_type") or "").strip()
    observations = [_trim_text(obs, 180) for obs in _as_list(result.get("observations"))[:4]]
    strategy_text = (result.get("strategy") or "").strip()
    insight = (result.get("insight") or "").strip()
    issues = []

    if persona not in ELITE_PERSONAS:
        issues.append("persona must be one of the defined elite personas")
    if hook_type not in ELITE_HOOK_TYPES:
        issues.append("hook_type must be one of the defined hook types")
    if len(observations) < 2:
        issues.append("need at least 2 concrete observations")
    for observation in observations[:2]:
        if _looks_generic_observation(observation):
            issues.append(f"observation is too generic: {observation}")
            break
    if len(strategy_text.split()) < 3:
        issues.append("strategy explanation is too thin")
    if len(insight.split()) < 3:
        issues.append("insight is too thin")

    word_count = len(email.split())
    if word_count < 90 or word_count > 210:
        issues.append(f"email must be 90-210 words, got {word_count}")

    if business_name and business_name.lower() not in email.lower():
        issues.append("email must mention the business name")

    if len(subject.split()) > 8:
        issues.append("subject is too long")

    lower_email = email.lower()
    lower_strategy = strategy_text.lower()
    lower_insight = insight.lower()

    if has_banned_phrases(subject) or has_banned_phrases(email):
        issues.append("email used banned phrasing")
    if any(phrase in lower_email or phrase in lower_strategy or phrase in lower_insight for phrase in ELITE_GENERIC_PHRASES):
        issues.append("generic phrase detected")
    if any(phrase in lower_email for phrase in ELITE_WEAK_CTA_PHRASES):
        issues.append("overused CTA detected")
    if not _has_low_friction_cta(email):
        issues.append("missing a low-friction CTA")

    persona_tokens = ELITE_PERSONA_REQUIRED_TOKENS.get(persona, [])
    if persona_tokens and not any(
        token in lower_email or token in lower_strategy or token in lower_insight
        for token in persona_tokens
    ):
        issues.append(f"{persona} angle is missing from the output")
    if persona == "Competitor Spy" and not (lead_data.get("competitors") or []):
        issues.append("competitor persona requires competitor context")

    specificity_tokens = _elite_specificity_tokens(lead_data)
    if specificity_tokens and not any(
        token in lower_email or token in lower_insight or token in lower_strategy
        for token in specificity_tokens[:12]
    ):
        issues.append("output is not using the scraped specifics")

    if observations and not any(
        _observation_is_used(observation, email, insight, strategy_text)
        for observation in observations[:2]
    ):
        issues.append("email is not carrying the extracted observations")

    return issues


def _clean_review_quote(review_text, limit=140):
    cleaned = re.sub(r"\s+", " ", str(review_text or "")).strip().strip('"').strip("'")
    if not cleaned:
        return ""
    cleaned = cleaned.rstrip(".")
    return _trim_text(cleaned, limit)


STRUCTURED_WEBSITE_EMAIL_PROMPT = """You are a professional cold email writing AI.

Generate a data-driven cold email using scraped Google Maps and website audit data.

INPUT:
- RecipientFirstName
- BusinessName
- Industry
- Location
- Website
- ServicesOffered
- Reviews
- ReviewSnippet
- ReviewSentiment
- CompetitorSignals
- ExactAuditIssue
- ReviewQuote
- WhyThisBusinessIsFit
- UniqueValueProposition
- CompetitorInsight
- LocalMarketIntelligence
- HomepageCTAQuality
- WebsiteIssue

STRUCTURE:
Paragraph 1: Personalized intro referencing the business and what makes them a strong fit
Paragraph 2: Direct observation about the exact audit issue and why it matters for this business
Paragraph 3: Clear unique value proposition + low-friction CTA
Signature

RULES:
- Use exact evidence from the input fields rather than vague language
- Mention the website directly when possible
- Reference one review quote or review score if available
- Explain why this business is a good fit and what is unique about the outreach
- Include competitor or local-market insight when present
- Keep tone helpful, concise, and not pushy
- Output only the email
- Paragraphs separated by one blank line
- No indentation
- Keep each paragraph to 1-2 sentences
"""


STRUCTURED_NO_WEBSITE_EMAIL_PROMPT = """You are a professional cold email writing AI.

Generate a high-converting cold email using scraped Google Maps data.

INPUT:
- RecipientFirstName
- BusinessName
- Industry
- Location
- ServicesOffered
- Reviews
- ReviewSnippet
- ReviewSentiment
- CompetitorSignals
- ExactAuditIssue
- ReviewQuote
- WhyThisBusinessIsFit
- UniqueValueProposition
- CompetitorInsight
- LocalMarketIntelligence
- Phone

STRUCTURE:
Paragraph 1: Personalized intro referencing business
Paragraph 2: Position the missing website as a growth opportunity and cite a specific issue if present
Paragraph 3: Value (simple online presence / lead capture) + low-friction CTA
Signature

RULES:
- Do NOT shame or criticize
- Position lack of website as a growth opportunity
- Keep tone helpful and practical
- Mention why this business is a good fit for a new website or listing improvement
- Include one unique value statement specific to this lead
- Use specific evidence fields when available
- Output only the email
- Paragraphs separated by one blank line
- No indentation
- Keep each paragraph to 1-2 sentences
"""


STRUCTURED_PERSONA_STYLE_GUIDANCE = {
    "Revenue Hacker": "Use a practical, commercially aware tone. Emphasize missed enquiries, lost jobs, or revenue leakage without sounding pushy.",
    "SEO Sniper": "Use a search-and-trust lens. Emphasize Google visibility, reviews, or search trust where relevant.",
    "CX Fixer": "Use a calm, customer-experience lens. Emphasize contact friction, booking friction, or unclear next steps.",
    "Automation Operator": "Use an efficiency lens. Emphasize manual follow-up, back-and-forth, admin drag, or wasted response time.",
    "Authority Builder": "Use a trust-and-positioning lens. Emphasize credibility, proof, premium feel, and specialist positioning.",
    "Competitor Spy": "Use a local-market lens. Emphasize competitor gaps, nearby alternatives, and why clarity wins first contact.",
}


def _select_structured_persona(lead_data):
    explicit = (
        lead_data.get("persona")
        or lead_data.get("selected_persona")
        or lead_data.get("preferred_persona")
    )
    if explicit in ELITE_PERSONAS:
        return explicit, ELITE_PERSONAS[explicit]

    persona_history = [p for p in (lead_data.get("persona_history") or []) if p in ELITE_PERSONAS]
    past_outcomes = [outcome.get("type") for outcome in (lead_data.get("past_outcomes") or []) if outcome.get("type")]

    if "opened" in past_outcomes and not any(x in past_outcomes for x in ["reply", "appointment_booked", "sale_closed"]):
        return "CX Fixer", ELITE_PERSONAS.get("CX Fixer", "Use a calm, customer-experience lens. Emphasize contact friction, booking friction, or unclear next steps.")

    if any(x in past_outcomes for x in ["reply", "appointment_booked", "sale_closed"]):
        last_persona = persona_history[0] if persona_history else None
        if last_persona in ELITE_PERSONAS:
            return last_persona, ELITE_PERSONAS.get(last_persona, "")

    persona_name = _choose_persona_by_history(persona_history, lead_data)
    return persona_name, ELITE_PERSONAS.get(persona_name, ELITE_PERSONAS.get(_default_elite_persona(lead_data), ""))


def _choose_persona_by_history(persona_history, lead_data):
    ordered_personas = list(ELITE_PERSONAS.keys())
    if not persona_history:
        return _default_elite_persona(lead_data)

    last_persona = persona_history[0]
    if last_persona not in ordered_personas:
        return _default_elite_persona(lead_data)

    next_index = (ordered_personas.index(last_persona) + 1) % len(ordered_personas)
    next_persona = ordered_personas[next_index]

    if len(persona_history) >= 2 and persona_history[1] == next_persona:
        next_persona = ordered_personas[(next_index + 1) % len(ordered_personas)]

    return next_persona


def _rotate_persona(current_persona, persona_history):
    ordered_personas = list(ELITE_PERSONAS.keys())
    last_persona = persona_history[0] if persona_history else None
    if not last_persona or last_persona not in ordered_personas:
        return current_persona

    if persona_history.count(last_persona) >= 2:
        next_index = (ordered_personas.index(last_persona) + 1) % len(ordered_personas)
        return ordered_personas[next_index]

    return current_persona


def _structured_persona_overlay(persona_name, has_website):
    base = STRUCTURED_PERSONA_STYLE_GUIDANCE.get(
        persona_name,
        "Use the selected persona as a tone and emphasis overlay while keeping the structure unchanged.",
    )
    website_line = (
        "Apply the persona mainly to the observation and value paragraphs, not the greeting."
        if has_website
        else "Apply the persona mainly to the missing-website opportunity and value paragraphs, not the greeting."
    )
    return f"{base} {website_line}"


def _structured_persona_value_line(persona_name, has_website):
    if persona_name == "Revenue Hacker":
        return (
            "That kind of friction can quietly cost quote-ready enquiries."
            if has_website
            else "That can quietly cost some ready-to-buy enquiries before they ever reach out."
        )
    if persona_name == "SEO Sniper":
        return (
            "When someone clicks through from Google after seeing strong reviews, the website has to cash that trust in quickly."
            if has_website
            else "Without a website, the Google listing has to carry all the search trust on its own."
        )
    if persona_name == "CX Fixer":
        return (
            "When someone wants help quickly, even one extra beat in the contact path creates friction."
            if has_website
            else "Some customers want a clearer next step than a listing alone can give them."
        )
    if persona_name == "Automation Operator":
        return (
            "When the first contact path is slower than it should be, simple intent turns into extra follow-up and admin."
            if has_website
            else "Without a simple page, first enquiries can turn into extra back-and-forth and wasted admin time."
        )
    if persona_name == "Authority Builder":
        return (
            "The reputation is already there, so the website should reinforce that specialist trust faster."
            if has_website
            else "A simple website can reinforce the trust and credibility your reviews are already building."
        )
    if persona_name == "Competitor Spy":
        return (
            "In local markets, the business with the clearer website usually wins the first comparison."
            if has_website
            else "In local markets, competitors with a clear website often look easier to choose at a glance."
        )
    return (
        "A small improvement here can make the first impression work harder."
        if has_website
        else "A simple website can make the first impression work harder for you."
    )


def _lead_services_offered(lead_data):
    services = []
    website_signals = lead_data.get("website_signals") or {}
    for item in (website_signals.get("services") or [])[:4]:
        text = _trim_text(item, 60)
        if text:
            services.append(text)

    if not services:
        description = _trim_text(lead_data.get("description"), 140)
        if description:
            services.append(description)

    if not services:
        services.append(_detect_service(lead_data.get("business_name"), lead_data.get("industry")))

    deduped = []
    seen = set()
    for item in services:
        key = str(item).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(str(item).strip())
        if len(deduped) >= 3:
            break
    return ", ".join(deduped)


def _lead_reviews_summary(lead_data):
    rating = lead_data.get("rating")
    review_count = lead_data.get("review_count")
    if rating and review_count:
        return f"{review_count} Google reviews at {rating} stars"
    if review_count:
        return f"{review_count} Google reviews"
    if rating:
        return f"{rating} star Google rating"
    return ""


def _website_observed_opportunity(lead_data):
    website_signals = lead_data.get("website_signals") or {}
    issues = _as_list(lead_data.get("audit_issues"))

    if website_signals.get("cta_visibility") == "unclear":
        return "the site does not make the next step especially clear on first view"
    if website_signals.get("website_mobile_friendly") is False:
        return "the mobile experience may make it harder for visitors to reach out quickly"
    if website_signals.get("contact_method") == "form":
        return "the site seems to lean on forms first, which can slow down quicker enquiries"
    if website_signals.get("homepage_summary"):
        return "the homepage could do a stronger job turning interested visitors into enquiries"

    for issue in issues:
        cleaned = _trim_text(str(issue).rstrip("."), 180)
        if cleaned:
            return cleaned[0].lower() + cleaned[1:] if len(cleaned) > 1 else cleaned.lower()

    if website_signals.get("page_speed_score") is not None:
        score = website_signals.get("page_speed_score")
        if score < 60:
            return "the site is loading slowly enough to lose visitors before they can enquire"

    return "there may be a small missed opportunity to turn more visitors into enquiries"


def _lead_review_snippet(lead_data):
    reviews = lead_data.get("reviews") or []
    if isinstance(reviews, str):
        reviews = [reviews]
    for review in reviews:
        cleaned = _clean_review_quote(review, limit=120)
        if cleaned:
            return cleaned
    sample = lead_data.get("sample_reviews")
    if sample and isinstance(sample, str):
        return _clean_review_quote(sample, limit=120)
    return ""


def _lead_review_sentiment(lead_data):
    rating = lead_data.get("rating")
    review_count = lead_data.get("review_count")
    if rating and review_count:
        return f"{rating}-star average from {review_count} reviews"
    if rating:
        return f"{rating}-star average"
    if review_count:
        return f"{review_count} reviews overall"
    return ""


def _competitor_summary(lead_data):
    competitors = lead_data.get("competitors") or lead_data.get("peer_competitors") or []
    if isinstance(competitors, str):
        competitors = [c.strip() for c in competitors.split(",") if c.strip()]
    if not competitors:
        return ""
    return ", ".join([str(c).strip() for c in competitors if c])[:180]


def _good_fit_reason(lead_data):
    industry = _detect_service(lead_data.get("business_name"), lead_data.get("industry"))
    rating = lead_data.get("rating")
    review_count = lead_data.get("review_count")
    if rating and review_count:
        return f"Because {lead_data.get('business_name')} already has strong local reviews for {industry}, there is a clear chance to turn more interest into booked jobs."
    if lead_data.get("description"):
        return _trim_text(f"Because their current listing already shows {lead_data.get('description')}, a slightly stronger follow-up path could win more enquiries.", 180)
    return f"Because local customers in {lead_data.get('city') or 'your area'} will compare businesses quickly, this should be a strong fit."


def _unique_value_proposition(lead_data):
    business_name = lead_data.get("business_name") or "this business"
    industry = _detect_service(lead_data.get("business_name"), lead_data.get("industry"))
    if lead_data.get("website"):
        return f"Helping {business_name} turn more Maps views into booked jobs with one simple first-change suggestion."
    return f"Helping {business_name} capture local demand even without a website by making their first contact path clearer and faster."


def _local_market_signal(lead_data):
    city = lead_data.get("city")
    competitors = _competitor_summary(lead_data)
    if competitors:
        return f"Local customers around {city or 'your area'} are likely comparing {competitors}."
    if city:
        return f"In {city}, nearby businesses are often chosen by whoever makes the first message easiest to act on."
    return ""


def _structured_prompt_payload(lead_data, has_website):
    review_quote = _lead_review_snippet(lead_data)
    audit_issues = _as_list(lead_data.get("audit_issues"))[:3]
    competitor_insight = _competitor_summary(lead_data)
    payload = {
        "RecipientFirstName": lead_data.get("first_name") or None,
        "BusinessName": lead_data.get("business_name") or None,
        "Industry": _detect_service(lead_data.get("business_name"), lead_data.get("industry")),
        "Location": lead_data.get("city") or None,
        "Website": lead_data.get("website") or None,
        "Phone": lead_data.get("phone") or None,
        "ServicesOffered": _lead_services_offered(lead_data),
        "Reviews": _lead_reviews_summary(lead_data),
        "ReviewSnippet": review_quote,
        "ReviewSentiment": _lead_review_sentiment(lead_data),
        "ExactAuditIssue": audit_issues[0] if audit_issues else None,
        "ReviewQuote": review_quote,
        "WhyThisBusinessIsFit": _good_fit_reason(lead_data),
        "UniqueValueProposition": _unique_value_proposition(lead_data),
        "CompetitorInsight": competitor_insight,
        "LocalMarketIntelligence": _local_market_signal(lead_data),
        "HomepageCTAQuality": lead_data.get("homepage_cta_quality"),
        "WebsiteIssue": _website_observed_opportunity(lead_data) if has_website else "No website is linked from the listing.",
        "ObservedOpportunity": _website_observed_opportunity(lead_data) if has_website else (
            "there is no website linked from the listing, so some interested customers may not have a clear place to learn more or enquire online"
        ),
        "PastOutcomes": ", ".join([outcome.get("type") for outcome in (lead_data.get("past_outcomes") or []) if outcome.get("type")]) or None,
    }
    return payload


def _build_structured_email_user_prompt(lead_data, has_website, persona_name=None, persona_desc=None):
    payload = _structured_prompt_payload(lead_data, has_website)
    if not persona_name or not persona_desc:
        persona_name, persona_desc = _select_structured_persona(lead_data)
    lines = ["Generate the cold email using this scraped lead data:"]
    for key, value in payload.items():
        if value:
            lines.append(f"- {key}: {value}")
    lines.append(f"- PersonaName: {persona_name}")
    lines.append(f"- PersonaFocus: {persona_desc}")
    lines.append(f"- PersonaStyle: {_structured_persona_overlay(persona_name, has_website)}")
    lines.append("")
    lines.append("Output only the ready-to-send email.")
    return "\n".join(lines)


def _clean_llm_email_output(text):
    body = (text or "").strip()
    if body.startswith("```"):
        body = re.sub(r"^```(?:text|markdown)?", "", body).strip()
        body = re.sub(r"```$", "", body).strip()

    cleaned_lines = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
            continue
        if line.lower().startswith("subject:"):
            continue
        if line.lower().startswith("email:"):
            line = line.split(":", 1)[1].strip()
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def _normalize_structured_email_body(body, lead_data):
    first_name = lead_data.get("first_name") or "there"

    cleaned = _sanitize_language(_clean_llm_email_output(body))
    parts = [part.strip() for part in re.split(r"\n\s*\n", cleaned) if part.strip()]
    if len(parts) >= 4 and any("best regards" in part.lower() for part in parts[-1:]):
        signature = parts.pop()
    else:
        signature = f"Best regards,\n{config.SENDER_NAME}"

    greeting = ""
    if parts and parts[0].lower().startswith("hi "):
        greeting = " ".join(parts.pop(0).split())

    paragraphs = []
    for part in parts:
        line = " ".join(part.split())
        if line:
            paragraphs.append(line)
        if len(paragraphs) >= 3:
            break

    if not paragraphs and not greeting:
        return ""

    intro = f"Hi {first_name},"
    if not greeting:
        greeting = intro

    formatted = []
    if greeting:
        formatted.append(greeting)
    for paragraph in paragraphs:
        formatted.append(paragraph)

    body_out = "\n\n".join(formatted)
    if config.SENDER_NAME not in signature:
        signature = f"Best regards,\n{config.SENDER_NAME}"

    return f"{body_out}\n\n{signature}".strip()


def _structured_email_quality_issues(body, lead_data, has_website, persona_name=None):
    issues = []
    text = (body or "").strip()
    if not text:
        return ["empty body"]

    business_name = (lead_data.get("business_name") or "").strip().lower()
    if business_name and business_name not in text.lower():
        issues.append("business name missing")

    if has_banned_phrases(text):
        issues.append("banned phrasing detected")

    if not _has_low_friction_cta(text):
        issues.append("missing low-friction cta")

    parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    body_parts = []
    for part in parts:
        lower_part = part.lower()
        if "best regards" in lower_part:
            continue
        if lower_part.startswith("hi "):
            continue
        body_parts.append(part)
    if len(body_parts) < 3:
        issues.append("needs 3 body paragraphs")

    lower = text.lower()
    if persona_name:
        markers = ELITE_PERSONA_REQUIRED_TOKENS.get(persona_name, [])
        if markers and not any(marker in lower for marker in markers):
            issues.append(f"{persona_name} logic is missing from the email")
    if has_website and not any(token in lower for token in ["website", "site", "homepage"]):
        issues.append("website lead email should reference the website")
    if not has_website and not any(
        token in lower for token in ["without a website", "no website", "could not find was a website", "operating without a website"]
    ):
        issues.append("no-website lead email should mention the missing website")

    return issues


def evaluate_structured_email_quality(body, lead_data, has_website, persona_name=None):
    issues = _structured_email_quality_issues(body, lead_data, has_website, persona_name=persona_name)
    score = max(0, 100 - len(issues) * 15)
    return {
        "score": score,
        "issues": issues,
        "has_personalization": not any(i in ["business name missing", "needs 3 body paragraphs"] for i in issues),
    }


def _build_structured_website_fallback(lead_data, persona_name=None):
    business_name = lead_data.get("business_name") or "your business"
    first_name = lead_data.get("first_name") or "there"
    trade = _detect_service(business_name, lead_data.get("industry"))
    city = lead_data.get("city") or "your area"
    services = _lead_services_offered(lead_data)
    reviews = _lead_reviews_summary(lead_data)
    opportunity = _website_observed_opportunity(lead_data)
    persona_line = _structured_persona_value_line(persona_name, True) if persona_name else ""

    intro = f"I came across {business_name} while exploring {trade} businesses in {city}."
    if reviews:
        intro += f" The reputation you already have there stood out, especially with {reviews}."

    observation = f"I noticed one website opportunity: {opportunity}."
    if services:
        observation += f" That matters when people are trying to understand services like {services} and decide quickly."
    if persona_line:
        observation += f" {persona_line}"

    cta = (
        "If helpful, I can share 1-2 quick ideas to tighten that up by email, "
        "no call needed."
    )

    body = "\n\n".join([
        f"Hi {first_name},",
        intro,
        observation,
        cta,
        f"Best regards,\n{config.SENDER_NAME}",
    ])
    return _normalize_structured_email_body(body, lead_data)


def _build_structured_no_website_fallback(lead_data, persona_name=None):
    business_name = lead_data.get("business_name") or "your business"
    first_name = lead_data.get("first_name") or "there"
    trade = _detect_service(business_name, lead_data.get("industry"))
    city = lead_data.get("city") or "your area"
    reviews = _lead_reviews_summary(lead_data)
    phone = lead_data.get("phone")
    persona_line = _structured_persona_value_line(persona_name, False) if persona_name else ""

    intro = f"I came across {business_name} while looking at {trade} businesses in {city}."
    if reviews:
        intro += f" You already seem to have strong local trust, with {reviews}."

    observation = (
        "I noticed you are currently operating without a website, "
        "which can make it harder for customers to learn more or reach out online."
    )
    if phone:
        observation += " That usually means the listing has to do all the work on its own."
    if persona_line:
        observation += f" {persona_line}"

    cta = (
        "If helpful, I can put together a simple page idea to showcase your services "
        "and capture new leads, and I can send a quick example by email."
    )

    body = "\n\n".join([
        f"Hi {first_name},",
        intro,
        observation,
        cta,
        f"Best regards,\n{config.SENDER_NAME}",
    ])
    return _normalize_structured_email_body(body, lead_data)


def generate_maps_cold_email(lead_data, country=None, max_retries=2):
    if not isinstance(lead_data, dict):
        raise ValueError("lead_data must be a dictionary")

    has_website = bool(lead_data.get("website"))
    persona_name, persona_desc = _select_structured_persona(lead_data)
    system_prompt = STRUCTURED_WEBSITE_EMAIL_PROMPT if has_website else STRUCTURED_NO_WEBSITE_EMAIL_PROMPT
    prompt_payload = _structured_prompt_payload(lead_data, has_website)
    user_prompt = _build_structured_email_user_prompt(
        lead_data,
        has_website,
        persona_name=persona_name,
        persona_desc=persona_desc,
    )
    business_name = lead_data.get("business_name") or "your business"
    subject = f"Quick note about {business_name}" if has_website else f"Quick idea for {business_name}"

    last_error = None
    for attempt in range(max(1, max_retries)):
        try:
            prompt = user_prompt
            if attempt > 0:
                prompt += "\n\nPlease revise the email and improve personalization and clarity."
            content, provider = _run_elite_llm(system_prompt, prompt, temperature=0.4, max_tokens=420)
            body = _normalize_structured_email_body(content, lead_data)
            if not body.strip():
                raise ValueError("LLM returned an empty email body")
            return {
                "persona": persona_name,
                "hook_type": "maps_context",
                "observations": [prompt_payload.get("ObservedOpportunity")],
                "strategy": (
                    f"Use the paragraph-form Maps prompt with the {persona_name.lower()} lens "
                    "while keeping the structure low-friction and personalized."
                ),
                "insight": prompt_payload.get("ObservedOpportunity"),
                "subject": subject,
                "email": body,
                "provider": provider,
            }
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"LLM generation failed after {max(1, max_retries)} attempt(s): {last_error}")


def _build_no_website_observations(lead_data):
    business_name = lead_data.get("business_name") or "This business"
    observations = []
    rating = lead_data.get("rating")
    review_count = lead_data.get("review_count")
    description = _trim_text(lead_data.get("description"), 180)
    phone = str(lead_data.get("phone") or "").strip()
    review_quote = ""
    for review in (lead_data.get("reviews") or [])[:3]:
        review_quote = _clean_review_quote(review)
        if review_quote:
            break

    if rating and review_count:
        observations.append(f"{business_name} already has {review_count} Google reviews at {rating} stars")
    elif review_count:
        observations.append(f"{business_name} already has {review_count} Google reviews")
    elif rating:
        observations.append(f"{business_name} is sitting at {rating} stars on Google")

    observations.append("No website is linked from the listing")

    if review_quote:
        observations.append(f'Review quote: "{review_quote}"')

    if description:
        observations.append(f"Directory description: {description.rstrip('.')}")

    if phone and phone.upper() != "N/A":
        observations.append("The listing appears to rely on calls as the main next step")

    deduped = []
    seen = set()
    for item in observations:
        key = item.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= 4:
            break
    return deduped


def generate_no_website_outreach(lead_data, country=None):
    if not isinstance(lead_data, dict):
        raise ValueError("lead_data must be a dictionary")

    business_name = lead_data.get("business_name") or "your business"
    first_name = lead_data.get("first_name") or "there"
    trade = _detect_service(business_name, lead_data.get("industry"))
    city = lead_data.get("city") or "your area"
    rating = lead_data.get("rating")
    review_count = lead_data.get("review_count")
    opportunity_score = lead_data.get("opportunity_score")
    observations = _build_no_website_observations(lead_data)

    review_quote = ""
    for observation in observations:
        if observation.startswith("Review quote:"):
            review_quote = observation.split(":", 1)[1].strip().strip('"')
            break

    reputation_line = f"{business_name} has already built a strong reputation locally."
    if rating and review_count:
        reputation_line = (
            f"I noticed {business_name} has already built a strong reputation locally, "
            f"with {review_count} Google reviews and a {rating} rating."
        )
    elif review_count:
        reputation_line = (
            f"I noticed {business_name} already has {review_count} Google reviews, "
            "which is a strong sign people are already finding and trusting you."
        )
    elif rating:
        reputation_line = f"I noticed {business_name} is already sitting at {rating} stars on Google."

    demand_line = (
        f"When someone finds a {trade} business on Google, they usually want to see services, "
        "check availability, and contact someone quickly."
    )
    gap_line = "One thing I could not find was a website."
    opportunity_line = (
        "Without a simple site, some of that intent can drop off before the person takes the next step."
    )
    quote_line = f'One review even said, "{review_quote}."' if review_quote else ""
    score_line = ""
    if opportunity_score is not None:
        score_line = (
            f"That stood out because the listing already looks like a real opportunity, "
            f"not a cold start."
        )
    cta_line = (
        f"If helpful, I can send over a quick homepage idea tailored to {business_name} "
        "so you can see what that could look like."
    )

    body = "\n\n".join(
        part
        for part in [
            f"Hi {first_name},",
            f"I came across {business_name} while looking at {trade} businesses in {city}.",
            reputation_line,
            gap_line,
            demand_line,
            quote_line,
            score_line,
            opportunity_line,
            cta_line,
            f"Best regards,\n{config.SENDER_NAME}",
        ]
        if part
    )

    subject, body = _finalize(
        f"Quick idea for {business_name}",
        body,
        business_name,
        trade,
        city,
        first_name,
    )

    return {
        "persona": "No Website Closer",
        "hook_type": "data_observation",
        "observations": observations,
        "strategy": (
            "Lead with existing demand and trust signals, point out the missing website, "
            "and offer a low-friction tailored homepage idea."
        ),
        "insight": "the business already has local demand, but there is no website converting that intent",
        "subject": subject,
        "email": body,
        "provider": "rule_based_no_website",
    }


def generate_elite_outreach(lead_data, country=None, max_retries=3):
    if not isinstance(lead_data, dict):
        raise ValueError("lead_data must be a dictionary")

    try:
        from core.pipeline import run_pipeline

        return run_pipeline(lead_data, country=country, max_retries=max_retries)
    except Exception as e:
        print(f"[Elite Pipeline] Falling back due to: {e}")
        return _build_fallback_elite_result(lead_data, country=country)

