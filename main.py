import time
import random
import json
import argparse
from urllib.parse import urlparse
import config
from scraper import Scraper
from database import DataManager
from mailer import Mailer
import llm_helper
import validator
import yelp_api_scraper
import concurrent.futures
import imap_tracker
import asyncio
from scraper import Scraper
from database import DataManager
from mailer import Mailer
import osm_scraper
from freedom_search import FreedomSearch
from yelp_scraper import extract_business_website
from scrapers_manager import run_parallel_scraping
from utils import canonicalize_website, pagespeed
try:
    from langchain_groq import ChatGroq
    from langgraph.graph import StateGraph, START, END
    from typing import TypedDict, Annotated
    from langgraph.graph.message import add_messages
    import chromadb
    from langfuse import Langfuse
    from fastapi import FastAPI, WebSocket
    import uvicorn
    import logfire
except Exception:
    ChatGroq = None
    StateGraph = None
    START = None
    END = None
    add_messages = None
    TypedDict = dict
    Annotated = list
    chromadb = None
    Langfuse = None
    FastAPI = None
    WebSocket = None
    uvicorn = None
    logfire = None

# --- FastAPI App for Koyeb Health Checks & Monitoring ---
app = None
if FastAPI:
    app = FastAPI(title="Website Sales Agent API")

    @app.get("/")
    @app.get("/health")
    def health_check():
        """Standard health check for Koyeb/PaaS."""
        return {"status": "healthy", "service": "website-sales-agent"}

    @app.get("/status")
    def site_status():
        """Returns the current status and activity count."""
        try:
            from database import DataManager

            dm = DataManager()
            return {"running": True, "daily_actions": dm.count_daily_actions()}
        except Exception as e:
            return {"running": True, "error": str(e)}

    @app.websocket("/ws/logs")
    async def logs(ws: WebSocket):
        await ws.accept()
        await ws.send_text("agent: connected")
        try:
            while True:
                await ws.send_text(f"tick:{time.time()}")
                await asyncio.sleep(1)
        except Exception:
            pass



def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--query", type=str, help='Single query like "Plumber near Chicago, IL, USA"')
    ap.add_argument("--niches", type=str, help="Comma-separated niches to target")
    ap.add_argument("--locations", type=str, help="Comma-separated locations to target")
    ap.add_argument("--session-queries", type=int, help="How many queries to run this session")
    ap.add_argument("--agent", action="store_true")
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--crew", action="store_true")
    ap.add_argument("--tech", type=str)
    ap.add_argument("--exclude-tech", type=str)
    ap.add_argument("--country", type=str)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--linkedin", action="store_true")
    ap.add_argument("--titles", type=str)
    ap.add_argument("--linkedin-profile", type=str)
    ap.add_argument("--signals", action="store_true")
    ap.add_argument("--niche", type=str)
    ap.add_argument("--location", type=str)
    ap.add_argument("--source", type=str)
    ap.add_argument("--role", type=str)
    ap.add_argument("--audit", action="store_true", help="Run Audit-First strategy")
    return ap.parse_args()

def log(event, **fields):
    payload = {"event": event, "ts": int(time.time()), **fields}
    print(json.dumps(payload))



def main():
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass
    print("Starting Sales Automation Agent...")
    
    # 1. Setup
    args = parse_args()
    if args.agent and ChatGroq and StateGraph:
        class State(TypedDict):
            messages: Annotated[list, add_messages]
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=config.GROQ_API_KEY)
        wf = StateGraph(State)
        def chatbot_node(state: dict):
            resp = llm.invoke(state["messages"])
            return {"messages": [resp]}
        wf.add_node("chatbot_node", chatbot_node)
        wf.add_edge(START, "chatbot_node")
        wf.add_edge("chatbot_node", END)
        app = wf.compile()
        mem_client = chromadb.Client() if chromadb else None
        lf = Langfuse() if Langfuse else None
        try:
            if logfire and getattr(config, "LOGFIRE_API_KEY", None):
                logfire.init(api_key=config.LOGFIRE_API_KEY)
        except Exception:
            pass
        for event in app.stream({"messages": [("user", "status and next actions")] }):
            for value in event.values():
                out = value["messages"][-1].content
                print(out)
                if mem_client:
                    try:
                        col = mem_client.get_or_create_collection(name="agent_memory")
                        col.add(documents=[out], ids=[str(time.time())])
                    except Exception:
                        pass
                if lf:
                    try:
                        lf.trace(name="agent_response", input=out)
                    except Exception:
                        pass
        return
    # CrewAI / Tech Search Legacy Blocks Removed
    # Use --tech with main loop instead.
    if args.serve and app and uvicorn:
        print(f"Starting API server on port {config.FASTAPI_PORT}...")
        uvicorn.run(app, host="0.0.0.0", port=config.FASTAPI_PORT)
        return
    if args.signals:
        dm = DataManager()
        smtp_accounts = config.get_smtp_accounts()
        mailers = [Mailer(a["email"], a["password"], a["server"], a["port"]) for a in smtp_accounts] or [Mailer("", "", config.SMTP_SERVER, config.SMTP_PORT)]
        mailer = mailers[0]
        niche = args.niche or getattr(config, "DEFAULT_TECH", "Shopify")
        location = args.location or "US"
        limit = args.limit or 20
        source = (args.source or "serpapi").lower()
        role = args.role or "Marketing Manager"
        import asyncio
        try:
            import httpx
        except Exception:
            httpx = None
        try:
            from serpapi import GoogleSearch
        except Exception:
            GoogleSearch = None
        titles = [t.strip().lower() for t in (args.titles or getattr(config, "DEFAULT_TITLES", "")).split(",") if t.strip()]
        async def serpapi_urls(q, loc, max_items):
            if GoogleSearch:
                try:
                    params = {"q": f"{q} near {loc}", "api_key": getattr(config, "SERPAPI_API_KEY", None)}
                    search = GoogleSearch(params)
                    result = search.get_dict()
                    urls = []
                    for r in result.get("organic_results", [])[:max_items]:
                        u = r.get("link")
                        if u:
                            urls.append(u)
                    return urls
                except Exception:
                    return []
            if not httpx or not getattr(config, "SERPAPI_API_KEY", None):
                return []
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get("https://serpapi.com/search", params={"engine":"google","q":f"{q} near {loc}","api_key":config.SERPAPI_API_KEY})
                if r.status_code != 200:
                    return []
                data = r.json()
                out = []
                for it in data.get("organic_results", [])[:max_items]:
                    u = it.get("link")
                    if u:
                        out.append(u)
                return out
        async def builtwith_domains(tech_name, country_code, max_items):
            api_key = getattr(config, "BUILTWITH_API_KEY", None)
            if not api_key or not httpx:
                return []
            url = "https://api.builtwith.com/v20/api.json"
            params = {"KEY": api_key, "TECH": tech_name, "COUNTRY": country_code, "META": "live"}
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url, params=params)
                if r.status_code != 200:
                    return []
                data = r.json()
                out = []
                l = data.get("Results", [])
                for row in l:
                    d = row.get("Domain")
                    if d:
                        out.append(d)
                    if len(out) >= max_items:
                        break
                return out
        async def fetch(url):
            if not httpx:
                return None
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                try:
                    r = await client.get(url, headers={"User-Agent":"Mozilla/5.0"})
                    return r
                except Exception:
                    return None
        def quick_observation(text):
            tx = (text or "").lower()
            if "tel:" not in tx and "call" not in tx:
                return "the call option wasn’t obvious on first view"
            if "contact" in tx and "book" not in tx and "schedule" not in tx:
                return "the booking step wasn’t immediately clear"
            if "phone" in tx and "footer" in tx:
                return "the phone number seemed easy to miss"
            return "the next step wasn’t obvious at first glance"
        def detect(url, r):
            triggers = []
            if r and r.url.scheme == "http":
                triggers.append("no_ssl")
            text = (r.text if r else "") or ""
            hdr = getattr(r, "headers", {}) or {}
            if "cdn.shopify.com" in text or "myshopify.com" in text:
                triggers.append("shopify")
            if "wp-content" in text or "wp-json" in text:
                triggers.append("wordpress")
            if "gtag(" not in text and "google-analytics" not in text:
                triggers.append("no_google_pixel")
            if "fbq(" not in text and "facebook.com/tr" not in text:
                triggers.append("no_fb_pixel")
            xp = (hdr.get("X-Powered-By") or hdr.get("x-powered-by") or "").lower()
            if xp.startswith("php/5") or "php/5." in xp:
                triggers.append("old_php")
            if "jquery-1." in text.lower():
                triggers.append("old_jquery")
            if "elementor" in text.lower() or "divi" in text.lower():
                triggers.append("wordpress_heavy_theme")
            if "<script type=\"application/ld+json\"" not in text and "schema.org" not in text:
                triggers.append("missing_schema")
            if ("cdn.shopify.com" in text or "myshopify.com" in text) and all(k not in text.lower() for k in ["apple pays", "apple pay", "applepaysession", "applepay"]):
                triggers.append("shopify_no_apple_pay")
            return triggers
        async def check_broken_checkout(url):
            if not httpx:
                return False
            try:
                async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
                    r = await client.get(url.rstrip("/") + "/cart", headers={"User-Agent":"Mozilla/5.0"})
                    if r.status_code >= 400:
                        return True
                    if "error" in (r.text or "").lower():
                        return True
            except Exception:
                return False
            return False
        class LeadScorer:
            def __init__(self):
                self.weights = {
                    "hiring_marketing": 50,
                    "no_ssl": 30,
                    "broken_checkout": 45,
                    "slow_pagespeed": 20,
                    "missing_pixel": 15,
                    "old_jquery": 10
                }
            def calculate_score(self, triggers_found):
                s = 0
                for t in triggers_found:
                    s += self.weights.get(t, 0)
                if s >= getattr(config, "SIGNALS_HOT_THRESHOLD", 80):
                    return "hot", s
                if s >= getattr(config, "SIGNALS_WARM_THRESHOLD", 40):
                    return "warm", s
                return "cold", s
        def score_triggers(triggers):
            weights = {
                "shopify": 2,
                "wordpress": 1,
                "no_google_pixel": 2,
                "no_fb_pixel": 2,
                "no_ssl": 3,
                "old_php": 3,
                "old_jquery": 2,
                "wordpress_heavy_theme": 2,
                "missing_schema": 1,
                "shopify_no_apple_pay": 2,
                "slow_pagespeed": 3,
            }
            score = 0
            for t in triggers:
                score += weights.get(t, 0)
            return score
        # pagespeed and other async functions moved to utils or shared scope

        async def hunter_search(domain):
            api_key = getattr(config, "HUNTER_API_KEY", None)
            if not httpx or not api_key:
                return []
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get("https://api.hunter.io/v2/domain-search", params={"domain":domain,"api_key":api_key})
                if r.status_code != 200:
                    return []
                data = r.json()
                emails = data.get("data", {}).get("emails", []) or []
                return [e.get("value") for e in emails[:3] if e.get("value")]
        async def snov_token():
            api_key = getattr(config, "SNOV_API_KEY", None)
            api_secret = getattr(config, "SNOV_API_SECRET", None)
            if not httpx or not api_key or not api_secret:
                return None
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post("https://api.snov.io/v1/oauth/access_token", data={"grant_type":"client_credentials","client_id":api_key,"client_secret":api_secret})
                if r.status_code != 200:
                    return None
                return r.json().get("access_token")
        async def snov_domain_emails(domain, token, titles_filter):
            if not httpx or not token:
                return []
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get("https://api.snov.io/v1/get-emails-from-domain", params={"domain":domain,"type":"all","limit":100}, headers={"Authorization":f"Bearer {token}"})
                if r.status_code != 200:
                    return []
                data = r.json()
                arr = data.get("emails") or []
                out = []
                for e in arr:
                    addr = e.get("email")
                    pos = (e.get("position") or "").lower()
                    if titles_filter:
                        if any(k in pos for k in titles_filter):
                            out.append(addr)
                    elif addr:
                        out.append(addr)
                return [x for x in out if x]
        async def proxycurl_enrich(linkedin_url):
            api_key = getattr(config, "PROXYCURL_API_KEY", None)
            if not httpx or not api_key or not linkedin_url:
                return None
            headers = {"Authorization": f"Bearer {api_key}"}
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get("https://api.proxycurl.com/v2/linkedin", params={"url": linkedin_url}, headers=headers)
                if r.status_code != 200:
                    return None
                data = r.json()
                company = None
                domain = None
                pos = None
                try:
                    ce = data.get("current_employment") or {}
                    company = (ce.get("company") or {}).get("name")
                    domain = (ce.get("company") or {}).get("website")
                    pos = (ce.get("title") or "").lower()
                except Exception:
                    pass
                return {"company": company, "domain": domain, "position": pos}
        async def serpapi_linkedin_profiles(role_q, loc, max_items):
            if not httpx and not GoogleSearch:
                return []
            if GoogleSearch:
                try:
                    params = {"q": f'site:linkedin.com/in \"{role_q}\" {loc}', "api_key": getattr(config, "SERPAPI_API_KEY", None)}
                    search = GoogleSearch(params)
                    result = search.get_dict()
                    urls = []
                    for r in result.get("organic_results", [])[:max_items]:
                        u = r.get("link")
                        if u and "linkedin.com/in/" in u:
                            urls.append(u)
                    return urls
                except Exception:
                    return []
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get("https://serpapi.com/search", params={"engine":"google","q":f'site:linkedin.com/in \"{role_q}\" {loc}',"api_key":config.SERPAPI_API_KEY})
                if r.status_code != 200:
                    return []
                data = r.json()
                out = []
                for it in data.get("organic_results", [])[:max_items]:
                    u = it.get("link")
                    if u and "linkedin.com/in/" in u:
                        out.append(u)
                return out
        async def run():
            if source == "builtwith":
                cc = "US"
                loc_lower = (location or "").lower()
                if "uk" in loc_lower:
                    cc = "UK"
                elif "au" in loc_lower or "australia" in loc_lower:
                    cc = "AU"
                elif "canada" in loc_lower:
                    cc = "CA"
                elif "germany" in loc_lower:
                    cc = "DE"
                domains = await builtwith_domains(niche, cc, limit)
                urls = [f"http://{d}" for d in domains]
            elif source == "jobboards":
                urls = await serpapi_linkedin_profiles(role, location, limit)
            else:
                urls = await serpapi_urls(niche, location, limit)
            tasks = []
            if source == "jobboards":
                tasks = [proxycurl_enrich(u) for u in urls]
            else:
                tasks = [fetch(u) for u in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            if source == "jobboards":
                for lp, enriched in zip(urls, results):
                    info = None if isinstance(enriched, Exception) else enriched
                    if not info or not info.get("domain"):
                        continue
                    d = info["domain"]
                    name = info.get("company") or d
                    emails = await hunter_search(d)
                    if not emails:
                        token = await snov_token()
                        emails = await snov_domain_emails(d, token, titles)
                    picked = None
                    for em in emails:
                        if mailer.validate_email_deep(em, smtp_probe=False):
                            picked = em
                            break
                    if picked:
                        subj = f"Quick idea for {name}"
                        body = f"Hi,\nI noticed a new {role} role and have a quick idea.\nWould you be open to a short email audit?\nThanks,\n{config.SENDER_NAME}"
                        if getattr(config, "DRY_RUN", False):
                            log("dry_send_preview", to=picked, subject=subj, body_preview=body[:200])
                            dm.record_email_event(name, "dry_preview", {"to": picked})
                        else:
                            mailer.send_email(picked, subj, body)
                            dm.log_action(name, "email_sent")
                print("Signals session finished.")
                return
            for u, r in zip(urls, results):
                resp = None if isinstance(r, Exception) else r
                t = detect(u, resp)
                ps, sc_path = await pagespeed(u) # unpacking tuple
                if ps is not None and ps < 0.4:
                    t.append("slow_pagespeed")
                if "shopify" in t:
                    try:
                        if await check_broken_checkout(u):
                            t.append("broken_checkout")
                    except Exception:
                        pass
                trig_for_score = list(t)
                if "no_google_pixel" in trig_for_score or "no_fb_pixel" in trig_for_score:
                    trig_for_score.append("missing_pixel")
                status, s_scorer = LeadScorer().calculate_score(trig_for_score)
                host = u.split("/")[2] if "://" in u else u
                if host.endswith(".gov") or host.endswith(".edu"):
                    s_scorer -= 20
                try:
                    age_days = dm.lead_age_days_by_website(u)
                    if age_days >= 30:
                        s_scorer -= 20
                except Exception:
                    pass
                s = score_triggers(t)
                if s < getattr(config, "SIGNALS_MIN_SCORE", 5):
                    continue
                name = u.split("/")[2] if "://" in u else u
                payload = {
                    "business_name": name,
                    "website": u,
                    "email": None,
                    "niche": niche,
                    "strategy": "signal",
                    "description": None,
                    "sample_reviews": None,
                    "audit_issues": ";".join(t)
                }
                dm.save_lead(payload)
                host = name
                picked = None
                emails = []
                try:
                    domain = host
                    emails = await hunter_search(domain)
                except Exception:
                    emails = []
                token = None
                if args.linkedin and not emails:
                    token = await snov_token()
                    try:
                        emails = await snov_domain_emails(host, token, titles)
                    except Exception:
                        pass
                if not emails:
                    cands = [f"info@{host}", f"contact@{host}", f"support@{host}"]
                    for c in cands:
                        try:
                            if mailer.validate_email_deep(c, smtp_probe=False):
                                picked = c
                                break
                        except Exception:
                            continue
                else:
                    for em in emails:
                        if mailer.validate_email_deep(em, smtp_probe=False):
                            picked = em
                            break
                if picked:
                    obs = quick_observation(getattr(resp, "text", ""))
                    subj, body = llm_helper.generate_email_master(name, niche, location, obs)
                    if getattr(config, "DRY_RUN", False):
                        log("dry_send_preview", to=picked, subject=subj, body_preview=body[:200])
                        dm.record_email_event(name, "dry_preview", {"to": picked})
                    else:
                        mailer.send_email(picked, subj, body)
                        dm.log_action(name, "email_sent")
            lp = getattr(args, "linkedin_profile", None)
            if lp:
                enriched = await proxycurl_enrich(lp)
                if enriched and enriched.get("domain"):
                    d = enriched["domain"]
                    name = enriched.get("company") or d
                    emails = await hunter_search(d)
                    if not emails:
                        token = await snov_token()
                        emails = await snov_domain_emails(d, token, titles)
                    for em in emails[:1]:
                        if mailer.validate_email_deep(em, smtp_probe=False):
                            subj = f"Quick idea for {name}"
                            body = f"Hi,\nI help companies improve conversions.\nWould you be open to a quick audit?\nThanks,\n{config.SENDER_NAME}"
                            if getattr(config, "DRY_RUN", False):
                                log("dry_send_preview", to=em, subject=subj, body_preview=body[:200])
                                dm.record_email_event(name, "dry_preview", {"to": em})
                            else:
                                mailer.send_email(em, subj, body)
                                dm.log_action(name, "email_sent")
            print("Signals session finished.")
        asyncio.run(run())
        return
    if args.dry_run:
        config.DRY_RUN = True
    dm = DataManager()
    smtp_accounts = config.get_smtp_accounts()
    mailers = [Mailer(a["email"], a["password"], a["server"], a["port"]) for a in smtp_accounts]
    mailer_index = 0
    mailer = mailers[0]
    
    # Initialize Scrapers
    scraper = Scraper(headless=config.HEADLESS) 
    yelp_api = yelp_api_scraper.YelpApiScraper()
    osm = osm_scraper.OsmScraper()
    osm = osm_scraper.OsmScraper()
    # apollo = apollo_scraper.ApolloScraper() # Removed
    
    cfg_issues = config.validate_config()
    if cfg_issues and not config.DRY_RUN:
        log("config_issues", issues=cfg_issues)
        config.DRY_RUN = True
    
    driver = scraper.get_driver()
    if not config.DRY_RUN:
        if not mailer.test_connection():
            print("[SMTP] Falling back to DRY_RUN due to connection failure.")
            config.DRY_RUN = True
    
    # 2. Daily Limit Check (DB Based)
    daily_count = dm.count_daily_actions()
    print(f"Daily actions so far: {daily_count}/{config.MAX_DAILY_ACTIONS}")
    
    # 3. Query Selection (Global Loop)
    if args.query:
        queries = [args.query]
    else:
        if args.niches or args.locations or args.niche or args.location:
            niches = [n.strip() for n in (args.niches or "").split(",") if n.strip()]
            if not niches and args.niche:
                niches = [args.niche]
            if not niches:
                niches = config.get_target_niches()

            locations = [l.strip() for l in (args.locations or "").split(",") if l.strip()]
            if not locations and args.location:
                locations = [args.location]
            if not locations:
                locations = config.get_target_locations()
                
            queries = [f"{n} near {l}" for n in niches for l in locations]
        else:
            queries = config.get_search_queries()
    print(f"Loaded {len(queries)} global search queries.")
    
    session_limit = args.session_queries if args.session_queries else config.SESSION_QUERIES
    session_queries = random.sample(queries, min(session_limit, len(queries)))
    
    for query in session_queries:
        if daily_count >= config.MAX_DAILY_ACTIONS:
            print("Daily limit reached (start of loop).")
            break
            
        print(f"\n--- Campaign: {query} ---")
        
        # Parallel Scraping
        leads_raw = run_parallel_scraping(query, scraper, driver, yelp_api, osm)
        
        # Fallback to Bing/YP if ABSOLUTELY nothing found (Sequential fallback still useful here as last resort)
        if len(leads_raw) == 0:
             print("All primary scrapers failed. Trying legacy fallbacks...")
             # ... (Keep legacy fallback logic if desired, or assume parallel covers it)
        
        # 4. Priority Sorting: No-website businesses first
        if config.PRIORITIZE_NO_WEBSITE:
            leads_no_site = [l for l in leads_raw if not l.get('website')]
            leads_with_site = [l for l in leads_raw if l.get('website')]
            leads_sorted = leads_no_site + leads_with_site
            print(f"  -> Prioritized: {len(leads_no_site)} no-website, {len(leads_with_site)} with-website")
        else:
            leads_sorted = leads_raw
        
        # 5. Process Leads (Dual Strategy)
        for lead_info in leads_sorted:
            # Re-check limit inside loop
            daily_count = dm.count_daily_actions()
            if daily_count >= config.MAX_DAILY_ACTIONS:
                print("Daily limit reached.")
                break
                
            name = lead_info['business_name']
            website = lead_info.get('website')
            # If Yelp API provided only Yelp URL, try to resolve business website
            if not website and lead_info.get('yelp_url'):
                try:
                    from yelp_scraper import extract_business_website
                    w = extract_business_website(lead_info.get('yelp_url'))
                    if w:
                        website = w
                        lead_info['website'] = w
                except Exception:
                    pass
            rating = lead_info.get('rating', 0)
            reviews = lead_info.get('review_count', 0)
            description = lead_info.get('description')
            sample_reviews = lead_info.get('sample_reviews')
            
            # Check DB existence
            if dm.lead_exists(name, website):
                continue
            
            # Strategy Filter (Rating-based, reviews optional)
            if rating < config.MIN_RATING:
                continue
                
            print(f"\nAnalyzing: {name} (Web: {website} | {rating}* ({reviews} reviews))")
            
            # Duplicate Detection: Check if website belongs to parent company
            parent_company_id = None
            normalized_website = canonicalize_website(website) if website else None
            if normalized_website and dm.is_parent_company(normalized_website):
                print(f"  → Duplicate website detected: {website}")
                parent_company_id = dm.get_parent_company_id(normalized_website)
                dm.increment_parent_company_count(normalized_website)
                # Save lead but don't email (parent already contacted)
                lead_info['parent_company_id'] = parent_company_id
                lead_info['city'] = query.split(" near ")[-1]
                lead_info['niche'] = query.split(" near ")[0]
                dm.save_lead(lead_info)
                print(f"  → Saved as duplicate, skipping email")
                continue
            
            strategy = "audit"
            audit_issues = []
            email = None
            first_name = None
            website_status = None
            screenshot_path = None
            
            # Branch A: No Website
            if not website:
                 strategy = "no_website"
                 print("  -> Strategy: NO WEBSITE (Reputation Pitch)")
                 email = lead_info.get('email') # Rare
            # Branch B: Website
            else:
                strategy = "audit"
                print("  -> Strategy: AUDIT (Redesign Pitch)")
                # Use scraper for basic info
                try:
                    email_site, audit_issues, web_signals = scraper.process_website(website)
                except Exception as e:
                    print(f"  -> Error processing website {website}: {e}")
                    continue
                
                # TECH FILTERING (New)
                if args.tech:
                    found_tech = web_signals.get("tech", [])
                    print(f"  -> Tech found: {found_tech}")
                    required_tech = args.tech.lower()
                    if not any(required_tech in t.lower() for t in found_tech):
                         print(f"  -> Skipping: Tech '{args.tech}' not found.")
                         continue
                
                # ENHANCED AUDIT (PageSpeed + Screenshot)
                score = None
                screenshot_path = None
                if getattr(config, "PAGESPEED_API_KEY", None):
                    try:
                        import asyncio
                        # Create new event loop for async call if needed, or run
                        score, screenshot_path = asyncio.run(pagespeed(website))
                        if score is not None:
                            if score < 0.5:
                                audit_issues.append(f"Google PageSpeed score is poor ({int(score * 100)}/100).")
                                strategy = "broken_site" # refined strategy name
                            print(f"  -> PageSpeed Score: {score}")
                    except Exception as e:
                        print(f"  -> PageSpeed Error: {e}")

                # FREEDOM SEARCH (Find CEO)
                # Combine site email with finding decision maker
                # Use FreedomSearch (reusing driver)
                fs = FreedomSearch(driver) 
                # Parse domain
                from urllib.parse import urlparse
                domain = urlparse(website).netloc.replace("www.", "")
                
                ceo_name = None
                email_person = None
                
                if args.audit or not email_site:
                    print("  -> Harnessing Freedom Search for CEO...")
                    ceo_name, ceo_profile = fs.find_ceo(name, lead_info.get('city'))
                    if ceo_name:
                        print(f"  -> Found CEO: {ceo_name}")
                        first_name = ceo_name.split()[0]
                        
                        # Guess emails
                        guessed = fs.guess_emails(ceo_name, domain)
                        for g in guessed:
                            if fs.verify_email_dns(g): # Simple DNS check
                                email_person = g
                                print(f"  -> Guessed & Verified Email: {email_person}")
                                break
                    else:
                         # Fallback to team page scraping
                         print("  -> Google X-Ray failed. Trying Team Page...")
                         contacts = fs.scrape_team_page(website)
                         if contacts:
                             # Pick first
                             c = contacts[0]
                             email_person = c.get('email')
                             print(f"  -> Found contact on Team/About page: {email_person}")
                    
                email = email_person or email_site
                
                # Register parent
                if normalized_website and not dm.is_parent_company(normalized_website):
                    parent_company_id = dm.create_parent_company(normalized_website, name)
                    lead_info['parent_company_id'] = parent_company_id
            
            if not email:
                print("  -> No email found on site.")
                # Safe fallback: try common inboxes on the business domain
                fallback_email = None
                domain = None
                try:
                    parsed = urlparse(canonicalize_website(website) or "")
                    domain = parsed.hostname
                except:
                    domain = None
                if domain:
                    candidates = [f"info@{domain}", f"support@{domain}", f"contact@{domain}", f"hello@{domain}", f"admin@{domain}"]
                    for cand in candidates:
                        try:
                            probe_ok = mailer.validate_email_deep(cand, smtp_probe=True)
                        except Exception:
                            probe_ok = False
                        if probe_ok:
                            fallback_email = cand
                            print(f"  -> Using validated fallback email: {fallback_email}")
                            break
                        # DNS-only fallback
                        dns_ok = mailer.validate_email_deep(cand, smtp_probe=False)
                        if dns_ok:
                            fallback_email = cand
                            print(f"  -> Using DNS-resolved fallback email: {fallback_email}")
                            break
                if not fallback_email:
                    print("  -> Skipping: no recipient email available.")
                    lead_info['strategy'] = strategy
                    lead_info['city'] = query.split(" near ")[-1]
                    lead_info['niche'] = query.split(" near ")[0]
                    dm.save_lead(lead_info)
                    continue
                else:
                    email = fallback_email
                
            print(f"  -> Email found: {email}")
                
            # Update Lead Object
            lead_info['email'] = email
            lead_info['audit_issues'] = "; ".join(audit_issues)
            lead_info['strategy'] = strategy
            lead_info['city'] = query.split(" near ")[-1]
            lead_info['niche'] = query.split(" near ")[0]
            
            # Save to DB
            dm.save_lead(lead_info)
            
            # 6. Email Generation (with personalization)
            time.sleep(random.uniform(1.2, 2.8))
            
            # Parse reviews from JSON
            import json
            reviews_list = json.loads(sample_reviews) if sample_reviews else []
            
            subject, body = llm_helper.generate_email_content(
                name, 
                lead_info['niche'], 
                lead_info['city'], 
                strategy, 
                audit_issues,
                description=description,
                reviews=reviews_list,
                first_name=first_name
            )
            # Quality gate
            score = 0
            try:
                score = llm_helper.score_email(subject, body)
            except Exception:
                score = 3
            tone = "A"
            try:
                tone = llm_helper.qa_tone(subject, body)
            except Exception:
                tone = "A"
            if llm_helper.has_banned_phrases(subject) or llm_helper.has_banned_phrases(body) or score < 3 or tone == "B":
                subject, body = llm_helper.generate_email_content(
                    name, 
                    lead_info['niche'], 
                    lead_info['city'], 
                    strategy, 
                    audit_issues,
                    description=description,
                    reviews=reviews_list,
                    first_name=first_name
                )
                try:
                    score = llm_helper.score_email(subject, body)
                except Exception:
                    score = 3
            if score < 3 or llm_helper.has_banned_phrases(subject) or llm_helper.has_banned_phrases(body) or llm_helper.qa_tone(subject, body) == "B":
                log("email_quality_reject", name=name, score=score)
                dm.record_email_event(name, "quality_reject", {"score": score})
                continue
            
            # Send
            sent = False
            import datetime
            try:
                s_h, s_m = map(int, config.EMAIL_WINDOW_START.split(":"))
                e_h, e_m = map(int, config.EMAIL_WINDOW_END.split(":"))
                now = datetime.datetime.now().time()
                start_t = datetime.time(s_h, s_m)
                end_t = datetime.time(e_h, e_m)
                in_window = start_t <= now <= end_t if start_t <= end_t else (now >= start_t or now <= end_t)
            except Exception:
                in_window = True
            if config.DRY_RUN:
                log("dry_send_preview", to=email, subject=subject, body_preview=body[:200])
                sent = True # Simulate success
            else:
                if not in_window:
                    log("email_skipped_window", to=email)
                    dm.record_email_event(name, "skipped_window", {"to": email})
                    continue
                
                mailer = mailers[mailer_index % len(mailers)]
                mailer_index += 1
                # Deep validation before sending
                # Prefer SMTP RCPT probe; if blocked, fall back to API + DNS
                probe_ok = False
                try:
                    probe_ok = mailer.validate_email_deep(email, smtp_probe=True)
                except Exception:
                    probe_ok = False
                api_ok = None
                try:
                    api_ok = validator.validate_email_api(email)
                except Exception:
                    api_ok = None
                dns_ok = mailer.validate_email_deep(email, smtp_probe=False)
                
                can_send = bool(probe_ok) or (api_ok is True) or (dns_ok and api_ok is None)
                
                if can_send:
                    sent = mailer.send_email(email, subject, body, attachment_paths=[screenshot_path] if screenshot_path else None)
                else:
                    print(f"[SMTP] Skipping {email} - Validation failed (probe={probe_ok}, api={api_ok}, dns={dns_ok}).")
                    log("email_skipped_validation", to=email, probe=probe_ok, api=api_ok, dns=dns_ok)
                    sent = False
                
                log("email_sent_result", to=email, sent=bool(sent), from_email=mailer.email)
                dm.record_email_event(name, "sent" if sent else "failed", {"to": email})
                try:
                    dm.record_training_example(name, subject, body, score, tone, "sent" if sent else "failed")
                except Exception:
                    pass
            
            if sent:
                 dm.log_action(name, "email_sent")
                 
                 # Human-Like Jitter
                 wait_time = random.randint(120, 360)
                 print(f"Email sent to {name}. Waiting {wait_time}s...")
                 time.sleep(wait_time)

                 # Batch Logic
                 emails_sent_in_batch += 1
                 if emails_sent_in_batch >= config.BATCH_SIZE:
                     print(f"\n[Pro Mode] Batch limit ({config.BATCH_SIZE}) reached. Resting for {config.BATCH_DELAY_MINUTES} minutes...")
                     print("This 'rest' period is critical for avoiding spam filters.")
                     time.sleep(config.BATCH_DELAY_MINUTES * 60)
                     emails_sent_in_batch = 0
                     
                 # Mark parent company as emailed
                 if website:
                     dm.mark_parent_company_emailed(canonicalize_website(website))
    
    # Optional: IMAP outcomes processing
    consecutive_bounces = 0
    try:
        events = imap_tracker.fetch_outcomes()
        for ev in events:
            if ev.get("type") == "bounce":
                consecutive_bounces += 1
                print(f"[ALERT] Bounce detected for {ev.get('email')}!")
                
            email_addr = ev.get("email")
            if email_addr:
                business = dm.get_business_name_by_email(email_addr)
                if business:
                    dm.record_email_event(business, ev.get("type"), ev.get("meta"))
                    log("email_outcome_recorded", type=ev.get("type"), email=email_addr, business=business)
                    try:
                        dm.set_training_outcome(business, ev.get("type"))
                    except Exception:
                        pass
                        
        if consecutive_bounces >= 3:
            print("\n[CRITICAL] Too many bounces detected (3+). Stopping agent to protect account reputation.")
            log("agent_stopped_safety", reason="excessive_bounces")
            try:
                scraper.cleanup()
                yelp_api.cleanup()
            except Exception:
                pass
            print("Agent stopped due to excessive bounces.")
            return
            
    except Exception as e:
        log("imap_processing_error", error=str(e))
                 
    # Cleanup driver safely using scraper's cleanup method
    scraper.cleanup()
    yelp_api.cleanup()
    print("Session finished.")

if __name__ == "__main__":
    main()
