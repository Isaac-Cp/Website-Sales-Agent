import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Security & API Keys ---
# CRITICAL: Never hardcode keys. They must be in the .env file.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YELP_API_KEY = os.getenv("YELP_API_KEY")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
CAPSOLVER_API_KEY = os.getenv("CAPSOLVER_API_KEY")
ANTICAPTCHA_API_KEY = os.getenv("ANTICAPTCHA_API_KEY")
BUILTWITH_API_KEY = os.getenv("BUILTWITH_API_KEY")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
PROXYCURL_API_KEY = os.getenv("PROXYCURL_API_KEY")
CLAY_API_KEY = os.getenv("CLAY_API_KEY")
FINDYMAIL_API_KEY = os.getenv("FINDYMAIL_API_KEY")
SNOV_API_KEY = os.getenv("SNOV_API_KEY")
SNOV_API_SECRET = os.getenv("SNOV_API_SECRET")
OUTSCRAPER_API_KEY = os.getenv("OUTSCRAPER_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

# --- IMAP Settings (for tracking bounces/replies) ---
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
IMAP_EMAIL = os.getenv("IMAP_EMAIL", SMTP_EMAIL)
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", SMTP_PASSWORD)
EMAIL_WINDOW_START = os.getenv("EMAIL_WINDOW_START", "00:00")
EMAIL_WINDOW_END = os.getenv("EMAIL_WINDOW_END", "23:59")

def get_smtp_accounts():
    """
    Returns a list of SMTP accounts.
    Supports loading from SMTP_ACCOUNTS_JSON env var or single account from .env.
    """
    accounts_json = os.getenv("SMTP_ACCOUNTS_JSON")
    if accounts_json:
        try:
            return json.loads(accounts_json)
        except json.JSONDecodeError:
            print("WARNING: Invalid JSON in SMTP_ACCOUNTS_JSON. Falling back to single account.")
            
    if SMTP_EMAIL and SMTP_PASSWORD:
        return [{
            "email": SMTP_EMAIL,
            "password": SMTP_PASSWORD,
            "server": SMTP_SERVER,
            "port": SMTP_PORT
        }]
    return []

def validate_config():
    """Checks for missing critical configuration."""
    issues = []
    if not GROQ_API_KEY and not OPENAI_API_KEY:
        issues.append("Missing LLM API Keys (GROQ_API_KEY or OPENAI_API_KEY)")
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        issues.append("Missing SMTP Credentials")
    return issues

if not GROQ_API_KEY and not OPENAI_API_KEY:
    print("WARNING: No LLM API Keys found in .env. Email generation will use generic templates.")

# --- Runtime Settings ---
DRY_RUN = False  # Emails will be sent if in window
HEADLESS = True  # Headless for reliability in automated runs
LOG_FILE = "activity.log"
SESSION_QUERIES = 6
PARALLEL_WORKERS = 6
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))
DEFAULT_TECH = os.getenv("DEFAULT_TECH", "Shopify")
DEFAULT_TITLES = os.getenv("DEFAULT_TITLES", "owner,ceo,founder,marketing director,sales director")
LOGFIRE_API_KEY = os.getenv("LOGFIRE_API_KEY")
PAGESPEED_API_KEY = os.getenv("PAGESPEED_API_KEY")
VALIDATION_PROVIDER = os.getenv("VALIDATION_PROVIDER", "hunter")

# --- Target Configuration ---
# High CPA Countries & Cities
TARGET_LOCATIONS = [
    "New York, NY, USA", "Los Angeles, CA, USA", "Chicago, IL, USA",
    "London, UK", "Manchester, UK",
    "Toronto, Canada", "Vancouver, Canada",
    "Sydney, Australia", "Melbourne, Australia",
    "Berlin, Germany", "Munich, Germany"
]

TARGET_NICHES = [
    "Plumber", "Electrician", "Carpenter", "HVAC", "Roofing",
    "Handyman", "Flooring", "Landscaper", "Painter", "Renovator",
    "Locksmith", "Garage Door Repair"
]

HIGH_NET_WORTH_CITIES = [
    "Beverly Hills, CA", "Upper East Side, NY", "Tribeca, NY", 
    "Atherton, CA", "Palm Beach, FL", "Scarsdale, NY", 
    "Greenwich, CT", "Medina, WA"
]

SCREENSHOT_DIR = "screenshots"


def get_target_locations():
    return TARGET_LOCATIONS

def get_target_niches():
    return TARGET_NICHES

def get_search_queries():
    """Generates a randomized list of search queries."""
    queries = []
    import random
    for niche in TARGET_NICHES:
        for location in TARGET_LOCATIONS:
            queries.append(f"{niche} near {location}")
    
    random.shuffle(queries)
    return queries

# --- Google Maps Settings ---
BASE_URL = "https://www.google.com/maps"
SCROLL_PAUSE_TIME = 2
MAX_LEADS_PER_QUERY = 15

# --- Filtering Thresholds ---
MIN_RATING = 0.0  # Allow leads without ratings
MIN_REVIEWS = 0   # Accept businesses even without reviews
PRIORITIZE_NO_WEBSITE = True  # Process no-website businesses first

# --- Selectors ---
# Note: Google Maps classes are obfuscated and change frequently.
# Reliability comes from robust searching strategies in scraper.py, not just these constants.
SELECTORS = {
    "result_container": "div[role='article']",
    "name_aria": "aria-label",
}

# --- Database ---
DB_FILE = "leads.db"
MAX_DAILY_ACTIONS = 40  # Daily email limit
DELAY_MIN = 120
DELAY_MAX = 360

# --- Batch Sending (Pro Mode) ---
BATCH_SIZE = 5          # Send 5 emails...
BATCH_DELAY_MINUTES = 30 # Then wait 30 minutes


# --- Sender Information ---
SENDER_NAME = "Promise"
SENDER_TITLE = "Web Developer & Designer"
FIVERR_LINK = "https://www.fiverr.com/s/Zmp9WLa"
SIGNALS_MIN_SCORE = int(os.getenv("SIGNALS_MIN_SCORE", 5))
SIGNALS_HOT_THRESHOLD = int(os.getenv("SIGNALS_HOT_THRESHOLD", 80))
SIGNALS_WARM_THRESHOLD = int(os.getenv("SIGNALS_WARM_THRESHOLD", 40))
