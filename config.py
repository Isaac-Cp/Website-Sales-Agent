import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
try:
    load_dotenv()
except Exception:
    pass  # Ignore if .env not found, like on cloud

# --- Security & API Keys ---
# CRITICAL: Never hardcode keys. They must be in the .env file.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
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
SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", 12))
SMTP_SSL_BYPASS_HOSTS = [
    host.strip().lower()
    for host in os.getenv("SMTP_SSL_BYPASS_HOSTS", "").split(",")
    if host.strip()
]

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
    Supports loading from SMTP_ACCOUNTS (comma-separated), SMTP_ACCOUNTS_JSON env var, or single account from .env.
    """
    # 1. Check for comma-separated string format
    accounts_str = os.getenv("SMTP_ACCOUNTS")
    if accounts_str:
        accounts = []
        for entry in accounts_str.split(","):
            parts = entry.strip().split(":")
            if len(parts) == 4:
                accounts.append({
                    "email": parts[0],
                    "password": parts[1],
                    "server": parts[2],
                    "port": int(parts[3])
                })
        if accounts:
            return accounts

    # 2. Check for JSON format
    accounts_json = os.getenv("SMTP_ACCOUNTS_JSON")
    if accounts_json:
        try:
            return json.loads(accounts_json)
        except json.JSONDecodeError:
            print("WARNING: Invalid JSON in SMTP_ACCOUNTS_JSON. Falling back to single account.")
            
    # 3. Fallback to single account
    if SMTP_EMAIL and SMTP_PASSWORD:
        return [{
            "email": SMTP_EMAIL,
            "password": SMTP_PASSWORD,
            "server": SMTP_SERVER,
            "port": SMTP_PORT
        }]
    return []

def get_optional_config_warnings():
    """Returns non-blocking warnings that shouldn't stop live sending."""
    issues = []
    if not GROQ_API_KEY and not OPENAI_API_KEY:
        issues.append("Missing LLM API Keys (GROQ_API_KEY or OPENAI_API_KEY)")
    return issues

def validate_config():
    """Checks for missing blocking configuration."""
    issues = []
    if not get_smtp_accounts():
        issues.append("Missing SMTP Credentials")
    return issues

if not GROQ_API_KEY and not OPENAI_API_KEY:
    print("WARNING: No LLM API Keys found in .env. Email generation will use generic templates.")

# --- Runtime Settings ---
DRY_RUN = False  # Emails will be sent if in window
ALLOW_RISKY_EMAILS = os.getenv("ALLOW_RISKY_EMAILS", "False").lower() == "true"
HEADLESS = True  # Headless for reliability in automated runs
LOG_FILE = "activity.log"
SESSION_QUERIES = 20
PARALLEL_WORKERS = 6
SKIP_JITTER = True
BATCH_SIZE = 100
BATCH_DELAY_MINUTES = 1
FASTAPI_PORT = int(os.getenv("PORT", os.getenv("FASTAPI_PORT", 8000)))
DATABASE_URL = os.getenv("DATABASE_URL")
DB_FILE = os.getenv("DB_FILE", "/var/data/leads.db" if os.path.isdir("/var/data") else "leads.db")
DEFAULT_TECH = os.getenv("DEFAULT_TECH", "Shopify")
DEFAULT_TITLES = os.getenv("DEFAULT_TITLES", "owner,ceo,founder,marketing director,sales director")
LOGFIRE_API_KEY = os.getenv("LOGFIRE_API_KEY")
PAGESPEED_API_KEY = os.getenv("PAGESPEED_API_KEY")
VALIDATION_PROVIDER = os.getenv("VALIDATION_PROVIDER", "hunter")
NO_WEBSITE_MIN_SCORE = int(os.getenv("NO_WEBSITE_MIN_SCORE", 50))
QUEUE_PHONE_ONLY_LEADS = os.getenv("QUEUE_PHONE_ONLY_LEADS", "True").lower() == "true"

# --- Target Configuration ---
# High CPA Countries & Cities
TARGET_LOCATIONS = [
    "New York, NY, USA", "Los Angeles, CA, USA", "Chicago, IL, USA",
    "Houston, TX, USA", "Phoenix, AZ, USA", "Philadelphia, PA, USA",
    "San Antonio, TX, USA", "San Diego, CA, USA", "Dallas, TX, USA",
    "San Jose, CA, USA", "Austin, TX, USA", "Jacksonville, FL, USA",
    "Fort Worth, TX, USA", "Columbus, OH, USA", "Charlotte, NC, USA"
]

TARGET_NICHES = [
    "Restaurant", "Hotel", "Bar", "Cafe", "Store", "Shop", "Mall",
    "Gym", "Dentist", "Lawyer", "Accountant", "Plumber", "Electrician",
    "Construction", "Real Estate Agent", "Insurance Agent", "Financial Advisor"
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
MAX_LEADS_PER_QUERY = 100

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
MAX_DAILY_ACTIONS = 600  # Daily email limit
MAX_DOMAIN_SENDS_PER_DAY = int(os.getenv("MAX_DOMAIN_SENDS_PER_DAY", 10))
MAX_CITY_SENDS_PER_DAY = int(os.getenv("MAX_CITY_SENDS_PER_DAY", 50))
MAX_PERSONA_SENDS_PER_DAY = int(os.getenv("MAX_PERSONA_SENDS_PER_DAY", 100))
FOLLOWUP_DELAY_DAYS = int(os.getenv("FOLLOWUP_DELAY_DAYS", 3))
FOLLOWUP_1_DELAY_DAYS = int(os.getenv("FOLLOWUP_1_DELAY_DAYS", 5))
FOLLOWUP_2_DELAY_DAYS = int(os.getenv("FOLLOWUP_2_DELAY_DAYS", 7))
OPENED_FOLLOWUP_DELAY_DAYS = int(os.getenv("OPENED_FOLLOWUP_DELAY_DAYS", 2))
BLACKLISTED_DOMAINS = [host.strip().lower() for host in os.getenv("BLACKLISTED_DOMAINS", "").split(",") if host.strip()]
BLACKLISTED_EMAILS = [addr.strip().lower() for addr in os.getenv("BLACKLISTED_EMAILS", "").split(",") if addr.strip()]
DELAY_MIN = 5
DELAY_MAX = 15

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
