import random


PERSONAS = {
    "Revenue Hacker": "Focus on lost revenue, missed conversions, pricing gaps",
    "SEO Sniper": "Focus on Google rankings, reviews, visibility gaps",
    "CX Fixer": "Focus on user confusion, friction, poor UX",
    "Automation Operator": "Focus on manual work, inefficiencies",
    "Authority Builder": "Focus on branding, trust, positioning",
    "Competitor Spy": "Focus on competitor advantages and gaps",
}


def get_persona(preferred=None, seed_text=None):
    if preferred in PERSONAS:
        return preferred, PERSONAS[preferred]

    options = list(PERSONAS.keys())
    rng = random.Random(seed_text or "")
    name = rng.choice(options)
    return name, PERSONAS[name]
