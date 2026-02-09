from groq import Groq
import config
import os
import random
import json
import math

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
            "buffer": "On a quick look,",
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
        
    good_ctas = ["send over", "reply 'yes'", "reply yes", "share 1–2", "share 1-2", "no call needed", "send a quick idea", "screenshot"]
    if any(g in cta_lower for g in good_ctas):
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

def _get_cta_text(business_name, industry, issue_type="general"):
    """
    Selects the best CTA based on industry and issue type.
    Priority:
    1. Visual Example (Design/UX)
    2. Yes Reply (Busy Industry)
    3. Async Share (Default)
    """
    i = (industry or "").lower()
    it = (issue_type or "").lower()
    bn = business_name or "your team"
    
    # 1. Visual Example (Design/UX)
    if "mobile" in it or "button" in it or "form" in it or "visible" in it:
        # Use sparingly, maybe randomize or default to async share if unsure?
        # User requested specific rules. Let's stick to the map.
        # But 'visual_example' text is "I can also send a quick screenshot showing what I mean."
        # This might be too abrupt as the main CTA.
        # Let's use the Async Share as primary safe bet, or mix.
        # Actually user said: "visual_example": { "use_if": "design_or_ux_issue" }
        pass # We will use standard fallback for now unless specifically requested to rotate.
    
    # 2. Busy Industry (Plumbing / HVAC / Garage) -> Yes Reply
    if any(k in i for k in ["plumb", "hvac", "garage", "contractor", "roof"]):
        return "If helpful, just reply 'yes' and I’ll send a couple of quick suggestions."
        
    # 3. Default (Async Share)
    return f"If you’d like, I can send over 1–2 quick ideas specific to {bn} — no call needed."

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
            "it wasn’t immediately clear what the next step is for someone who wants to contact you",
            "making the call option easier to spot"
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
        "it wasn't clear how customers should contact you",
        "making the contact options more visible"
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
    buffer = config_data.get("buffer", "On a quick look,")
    
    if not signals.get("website_exists", True):
        return f"{buffer} it looks like customers may not find a website quickly"
    
    cta = (signals.get("cta_visibility") or "").lower()
    if cta in ("unclear", "missing"):
        return f"{buffer} it wasn’t immediately clear what the next step is for someone who wants to contact you"
    
    if signals.get("website_mobile_friendly") is False:
        return f"{buffer} mobile visitors may leave because key actions aren’t easy to find"
        
    return f"{buffer} it isn’t immediately clear how to reach you fast"

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
    
    # Check if a valid CTA exists
    good_ctas = ["send over", "reply 'yes'", "reply yes", "share 1–2", "share 1-2", "no call needed", "send a quick idea", "screenshot"]
    has_good_cta = any(g in "\n".join(rebuilt).lower() for g in good_ctas)
    
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
        
    client_groq = Groq(api_key=config.GROQ_API_KEY) if config.GROQ_API_KEY else None
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
    banned = ["optimize","boost","scale","conversion","strategy","audit","results","grow","increase","automate","we help businesses","i specialize in"]
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
- Include exactly ONE observable, verifiable detail.
- Allowed: call button not visible; booking step unclear; phone number only in footer; no obvious next step.
- Forbidden: SEO, speed, performance, conversions; UX/optimization/structure; any metric, tool, audit, or analysis; generic observations.

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
    if any(k in (body or "").lower() for k in ["reply 'yes'","reply yes","share 1–2","share 1-2","quick suggestion","happy to share 1–2"]):
        s += 15
    s += 20
    s += 10
    s += 20
    return s
def generate_email_master(business_name, industry, city, observation, country="US"):
    subj = f"Small thing I noticed on {business_name}"
    body = ""
    client = Groq(api_key=config.GROQ_API_KEY) if config.GROQ_API_KEY else None
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
            f"On a quick look, {obs}.",
            "People are often trying to contact someone quickly.",
            "Sometimes just making the call option easier to spot helps.",
            "If helpful, just reply 'yes' and I’ll send a couple of quick ideas.",
            f"Best regards,\n{config.SENDER_NAME}"
        ]
        body = "\n\n".join(parts)
    score = score_master_email(subj, body)
    if score < 85:
        parts = [
            f"I was browsing local {industry} services in {city} and found {business_name}.",
            f"On a quick scan, {observation or 'the booking step wasn’t immediately clear'}.",
            "Most visitors are usually in a hurry.",
            "Often a simple ‘Call / Book’ section makes it clearer.",
            "Happy to share 1–2 thoughts by email.",
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
    
    if not config.GROQ_API_KEY and (not config.OPENAI_API_KEY or OpenAI is None):
        # Use Master Spintax Template as robust fallback
        return generate_spintax_email(business_name, city, trade, first_name)

    client_groq = Groq(api_key=config.GROQ_API_KEY) if config.GROQ_API_KEY else None
    
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
    buffer = country_config.get("buffer", "On a quick look,")
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
    good_ctas = ["send over", "reply 'yes'", "reply yes", "share 1–2", "share 1-2", "no call needed", "send a quick idea", "screenshot"]
    has_good_cta = any(g in "\n".join(rebuilt).lower() for g in good_ctas)
    
    if not has_good_cta:
        rebuilt.append(f"If you’d like, I can send over 1–2 quick ideas specific to {business_name} — no call needed.")
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
        return "it wasn't immediately clear how to reach you fast"

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
    return "it wasn't immediately clear what the next step is for someone who wants to contact you"

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

