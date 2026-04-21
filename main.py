import time
import random
import json
import argparse
import os
from urllib.parse import urlparse
import config
from scraper import Scraper
from database import DataManager
from mailer import Mailer, build_smtp_pool
from validator import get_email_validator
import llm_helper
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
from core.pipeline import run_pipeline
from bot_manager import BotManager
from dashboard_data import build_dashboard_payload, get_dashboard_lead_detail
from web_ui import render_dashboard_shell
try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None
except Exception:
    ChatGroq = None

try:
    from langgraph.graph import StateGraph, START, END
    from typing import TypedDict, Annotated
    from langgraph.graph.message import add_messages
except Exception:
    StateGraph = None
    START = None
    END = None
    add_messages = None
    TypedDict = dict
    Annotated = list

try:
    import chromadb
except Exception:
    chromadb = None

try:
    from langfuse import Langfuse
except Exception:
    Langfuse = None

try:
    from fastapi import FastAPI, HTTPException, WebSocket
    from fastapi.responses import HTMLResponse
except Exception:
    FastAPI = None
    HTTPException = None
    WebSocket = None
    HTMLResponse = None

try:
    import uvicorn
except Exception:
    uvicorn = None

try:
    import logfire
except Exception:
    logfire = None

APP_BOOT_TS = time.time()
BOT_MANAGER = BotManager(__file__)


def build_dashboard_response(recent_limit=24, event_limit=60, due_limit=18, top_limit=12):
    dm = DataManager()
    payload = build_dashboard_payload(
        dm,
        APP_BOOT_TS,
        recent_limit=recent_limit,
        event_limit=event_limit,
        due_limit=due_limit,
        top_limit=top_limit,
    )
    automation = BOT_MANAGER.snapshot()
    warnings = []
    config_issues = config.validate_config()
    runtime = payload.get("runtime", {})
    overview = payload.get("overview", {})
    health = payload.get("health", {})
    integrations = runtime.get("integrations") or {}
    email_window = runtime.get("email_window") or {}
    proof = payload.get("proof_of_outreach") or {}
    notifications = list(payload.get("notifications") or [])
    recent_runs = list(automation.get("recent_runs") or [])

    total_leads = _safe_int(overview.get("total_leads"), 0)
    with_email = _safe_int(overview.get("with_email"), 0)
    daily_actions = _safe_int(overview.get("daily_actions"), 0)
    daily_remaining = max(0, _safe_int(overview.get("daily_remaining"), 0))
    due_followups = _safe_int(overview.get("due_followups"), 0)
    risk_total = _safe_int(health.get("risk_total"), 0)
    sent_total = _safe_int(health.get("sent_total"), 0)
    max_daily_actions = _safe_int(runtime.get("max_daily_actions"), 0)
    smtp_ready = bool(integrations.get("smtp_ready"))
    llm_ready = bool(integrations.get("groq") or integrations.get("openai"))
    email_window_open = email_window.get("is_open")
    bot_enabled = bool(automation.get("enabled"))
    bot_status = automation.get("status")
    last_live_send = proof.get("last_live_send") or {}
    last_generated = proof.get("last_generated") or {}
    last_signal = proof.get("last_outreach_signal") or {}
    last_run = recent_runs[0] if recent_runs else None

    hard_blockers = []
    soft_blockers = []
    action_items = []

    if bot_status == "error":
        hard_blockers.append("The background runner failed on its last attempt.")
        action_items.append(
            {
                "level": "error",
                "title": "Inspect the latest bot failure",
                "message": automation.get("last_error") or "Open the bot runtime panel and review the last captured output before the next run.",
            }
        )

    if not smtp_ready:
        hard_blockers.append("SMTP is not configured, so the bot cannot send live emails.")
        action_items.append(
            {
                "level": "error",
                "title": "Connect a sending mailbox",
                "message": "Set SMTP_EMAIL and SMTP_PASSWORD, or provide SMTP_ACCOUNTS / SMTP_ACCOUNTS_JSON so live sending can start.",
            }
        )

    if max_daily_actions and daily_remaining <= 0:
        hard_blockers.append("The daily action budget is exhausted.")
        action_items.append(
            {
                "level": "warn",
                "title": "Daily sending limit reached",
                "message": f"The bot has already recorded {daily_actions} of {max_daily_actions} allowed daily actions. Sending resumes after the daily counters reset.",
            }
        )

    if email_window_open is False:
        soft_blockers.append("The configured email send window is currently closed.")
        action_items.append(
            {
                "level": "info",
                "title": "Wait for the next send window",
                "message": f"Live sending is paused outside {email_window.get('start') or '--'} - {email_window.get('end') or '--'}. The runner can still queue work and will send when the window reopens.",
            }
        )

    if not bot_enabled:
        soft_blockers.append("Bot autostart is disabled, so the dashboard will not launch runs automatically.")
        action_items.append(
            {
                "level": "warn",
                "title": "Enable automatic bot runs",
                "message": "Set BOT_AUTOSTART=true to let Render keep the outreach loop running, or keep using Run Bot Now from the dashboard.",
            }
        )

    if total_leads == 0:
        soft_blockers.append("No leads have been collected yet.")
        action_items.append(
            {
                "level": "warn",
                "title": "Collect the first leads",
                "message": "Use Run Bot Now after setting BOT_QUERY or your niche/location inputs so the bot has businesses to work on.",
            }
        )
    elif with_email == 0:
        soft_blockers.append("Leads exist, but none currently have direct email contacts.")
        action_items.append(
            {
                "level": "warn",
                "title": "Increase contact coverage",
                "message": "The bot has leads saved, but zero verified email contacts. Sending cannot start until email discovery succeeds for at least some leads.",
            }
        )

    if due_followups > 0:
        action_items.append(
            {
                "level": "info",
                "title": "Follow-ups are waiting",
                "message": f"{due_followups} lead(s) are due for the next touch. Those are the fastest opportunities to reactivate before scraping more cold leads.",
            }
        )

    if risk_total > 0:
        action_items.append(
            {
                "level": "warn",
                "title": "Review delivery risk",
                "message": f"There are {risk_total} bounce or unsubscribe signal(s) in the history. Review the affected leads and refine targeting before scaling volume.",
            }
        )

    if not llm_ready:
        action_items.append(
            {
                "level": "info",
                "title": "Add an LLM key for stronger copy",
                "message": "The bot can still send with generic templates, but adding GROQ_API_KEY or OPENAI_API_KEY will improve email quality and personalization.",
            }
        )

    if hard_blockers:
        readiness_status = "blocked"
        readiness_summary = "The dashboard is live, but live outreach is currently blocked by one or more operational issues."
    elif soft_blockers or sent_total == 0:
        readiness_status = "attention"
        readiness_summary = "The bot can run, but there are still a few conditions worth fixing before outreach will feel reliable."
    else:
        readiness_status = "ready"
        readiness_summary = "The bot is active, the system is configured for live sending, and recent activity suggests the loop is healthy."

    if bot_status == "running":
        pulse_status = "active"
        pulse_title = "Outreach loop is running now"
        pulse_message = "The background runner is actively processing a bot session right now."
    elif last_live_send.get("timestamp"):
        pulse_status = "working"
        pulse_title = "Live outreach is working"
        pulse_message = f"The last recorded live send was for {last_live_send.get('business_name') or 'a lead'} at {last_live_send.get('timestamp')}."
    elif last_generated.get("timestamp"):
        pulse_status = "warming"
        pulse_title = "Outreach generation is working"
        pulse_message = f"The bot is generating outreach activity, but the latest stored signal is {last_generated.get('event_type') or 'generation'} rather than a confirmed live send."
    elif last_run and last_run.get("status") == "success":
        pulse_status = "warming"
        pulse_title = "The runner is working, but no send was recorded yet"
        pulse_message = "A recent bot run finished successfully, so the loop is alive, but the database still shows zero live sends for that run."
    elif bot_status == "error":
        pulse_status = "blocked"
        pulse_title = "Outreach is blocked by a runner error"
        pulse_message = automation.get("last_error") or "The last bot run failed before it could complete."
    else:
        pulse_status = "idle"
        pulse_title = "Outreach has not shown proof of work yet"
        pulse_message = "The dashboard is online, but there is not yet a recent run, send, or generated outreach signal to prove activity."

    readiness_checks = [
        {
            "label": "Background runner",
            "status": "good" if bot_enabled else "warn",
            "detail": automation.get("message") or ("Automatic runs are enabled." if bot_enabled else "Automatic runs are disabled."),
        },
        {
            "label": "SMTP sending",
            "status": "good" if smtp_ready else "bad",
            "detail": f"{_safe_int(integrations.get('smtp_accounts'), 0)} sending account(s) detected." if smtp_ready else "No SMTP account is configured for live delivery.",
        },
        {
            "label": "Email window",
            "status": "good" if email_window_open is True else "warn",
            "detail": "The configured send window is open right now." if email_window_open is True else f"Current window: {email_window.get('start') or '--'} - {email_window.get('end') or '--'}.",
        },
        {
            "label": "Daily send budget",
            "status": "good" if daily_remaining > 0 or not max_daily_actions else "bad",
            "detail": f"{daily_remaining} action(s) remain out of {max_daily_actions or 'unlimited'} for today.",
        },
        {
            "label": "Lead contact coverage",
            "status": "good" if with_email > 0 else ("warn" if total_leads > 0 else "bad"),
            "detail": f"{with_email} of {total_leads} stored lead(s) currently have an email contact.",
        },
        {
            "label": "Content generation",
            "status": "good" if llm_ready else "warn",
            "detail": "An LLM key is configured for personalized copy." if llm_ready else "No LLM key detected, so the bot will fall back to generic templates.",
        },
    ]

    if sent_total == 0:
        if bot_status in {"disabled", "queued"}:
            warnings.append(
                {
                    "level": "warn",
                    "title": "Bot has not started running yet",
                    "message": automation.get("message") or "The dashboard is live, but the outreach runner is not active.",
                }
            )
        elif bot_status == "running":
            warnings.append(
                {
                    "level": "info",
                    "title": "First outreach run is in progress",
                    "message": "The bot is currently running, so the dashboard may still show zero sent emails until the session finishes.",
                }
            )
        elif bot_status == "error":
            warnings.append(
                {
                    "level": "error",
                    "title": "Bot runner hit an error",
                    "message": automation.get("last_error") or automation.get("message") or "The background bot session failed before it could send email.",
                }
            )
        elif bot_status == "sleeping" and automation.get("last_run_finished_at"):
            warnings.append(
                {
                    "level": "info",
                    "title": "Bot ran but has not sent email yet",
                    "message": "The runner completed a session, but zero emails have been recorded so far. Common reasons are no validated leads, missing SMTP credentials, send-window limits, or all candidates being throttled or filtered out.",
                }
        )

    if config.DRY_RUN:
        warnings.append(
            {
                "level": "warn",
                "title": "Dry run mode is enabled",
                "message": "The bot will generate previews but will not send live emails while DRY_RUN is true.",
            }
        )

    if not smtp_ready:
        warnings.append(
            {
                "level": "error",
                "title": "SMTP is not configured",
                "message": "Without SMTP credentials, the bot will not deliver live emails. Configure SMTP_EMAIL / SMTP_PASSWORD or SMTP_ACCOUNTS before expecting sends.",
            }
        )

    if email_window_open is False:
        warnings.append(
            {
                "level": "warn",
                "title": "Sending window is closed",
                "message": f"Email delivery is paused outside {email_window.get('start') or '--'} - {email_window.get('end') or '--'}.",
            }
        )

    if max_daily_actions and daily_remaining <= 0:
        warnings.append(
            {
                "level": "warn",
                "title": "Daily action limit reached",
                "message": f"The bot has used {daily_actions} of {max_daily_actions} allowed actions for today.",
            }
        )

    if total_leads == 0:
        warnings.append(
            {
                "level": "warn",
                "title": "No leads are stored yet",
                "message": "The bot needs at least one query, niche, or location configuration before it can discover leads and start outreach.",
            }
        )
    elif with_email == 0:
        warnings.append(
            {
                "level": "warn",
                "title": "No leads have email contacts yet",
                "message": "Leads are being stored, but none currently have a direct email. Outreach will stay at zero until email discovery succeeds.",
            }
        )

    if pulse_status in {"working", "active"}:
        notifications.insert(
            0,
            {
                "level": "good",
                "title": pulse_title,
                "message": pulse_message,
                "timestamp": last_live_send.get("timestamp") or last_signal.get("timestamp") or automation.get("last_run_started_at"),
            },
        )
    elif pulse_status == "blocked":
        notifications.insert(
            0,
            {
                "level": "error",
                "title": pulse_title,
                "message": pulse_message,
                "timestamp": automation.get("last_run_finished_at") or automation.get("last_run_started_at"),
            },
        )

    for run in recent_runs[:3]:
        if run.get("status") == "success":
            notifications.append(
                {
                    "level": "info" if not run.get("emails_sent") else "good",
                    "title": "Bot run completed",
                    "message": f"{run.get('emails_sent') or 0} email(s) sent in the latest {run.get('trigger') or 'scheduled'} run.",
                    "timestamp": run.get("finished_at"),
                }
            )
            break

    for issue in config_issues:
        warnings.append(
            {
                "level": "error",
                "title": "Configuration issue",
                "message": issue,
            }
        )

    payload["automation"] = automation
    payload["proof_of_outreach"] = {
        **proof,
        "pulse_status": pulse_status,
        "pulse_title": pulse_title,
        "pulse_message": pulse_message,
        "last_run": last_run,
    }
    payload["readiness"] = {
        "status": readiness_status,
        "summary": readiness_summary,
        "blockers": hard_blockers + soft_blockers,
        "checks": readiness_checks,
    }
    payload["action_items"] = action_items[:6]
    payload["notifications"] = notifications[:10]
    payload["warnings"] = warnings
    return payload

# --- FastAPI App for Koyeb Health Checks & Monitoring ---
app = None
if FastAPI:
    app = FastAPI(title="Website Sales Agent API")

    def service_snapshot():
        snapshot = {
            "status": "healthy",
            "service": "website-sales-agent",
            "running": True,
            "mode": "web-dashboard",
            "booted_at": APP_BOOT_TS,
        }
        try:
            dm = DataManager()
            dashboard = build_dashboard_payload(dm, APP_BOOT_TS, recent_limit=4, event_limit=4, due_limit=4, top_limit=4)
            snapshot["daily_actions"] = dashboard["overview"]["daily_actions"]
            snapshot["due_followups"] = dashboard["overview"]["due_followups"]
            snapshot["total_leads"] = dashboard["overview"]["total_leads"]
            snapshot["bot_status"] = BOT_MANAGER.snapshot().get("status")
        except Exception as e:
            snapshot["error"] = str(e)
        return snapshot

    @app.on_event("startup")
    async def app_startup():
        BOT_MANAGER.start()

    @app.on_event("shutdown")
    async def app_shutdown():
        BOT_MANAGER.stop()

    @app.get("/", response_class=HTMLResponse)
    def homepage():
        """Dashboard home for the web deployment."""
        return HTMLResponse(render_dashboard_shell())

    @app.get("/health")
    def health_check():
        """Standard health check for Koyeb/PaaS."""
        return {"status": "healthy", "service": "website-sales-agent"}

    @app.get("/status")
    def site_status():
        """Returns the current status and activity count."""
        return service_snapshot()

    @app.get("/api/dashboard")
    def dashboard_data():
        return build_dashboard_response()

    @app.get("/api/dashboard/leads/{lead_id}")
    def dashboard_lead_detail(lead_id: int):
        dm = DataManager()
        detail = get_dashboard_lead_detail(dm, lead_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Lead not found")
        return detail

    @app.get("/api/bot/status")
    def bot_status():
        return BOT_MANAGER.snapshot()

    @app.post("/api/bot/run-now")
    def bot_run_now():
        return BOT_MANAGER.request_run_now()

    @app.post("/api/bot/pause")
    def bot_pause():
        return BOT_MANAGER.pause()

    @app.post("/api/bot/resume")
    def bot_resume():
        return BOT_MANAGER.resume()

    @app.post("/api/bot/interval/{seconds}")
    def bot_set_interval(seconds: int):
        return BOT_MANAGER.set_loop_interval(seconds)

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
    ap.add_argument("--batch", action="store_true", help="Process existing leads from database instead of scraping")
    return ap.parse_args()

def log(event, **fields):
    payload = {"event": event, "ts": int(time.time()), **fields}
    print(json.dumps(payload))


def _normalized_text(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() in {"N/A", "NONE", "NULL", "UNKNOWN"}:
        return None
    return text


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def has_website(lead):
    return bool(_normalized_text((lead or {}).get("website")))


def has_email_contact(lead):
    return bool(_normalized_text((lead or {}).get("email")))


def has_phone_contact(lead):
    return bool(_normalized_text((lead or {}).get("phone")))


def classify_lead(lead):
    return "has_website" if has_website(lead) else "no_website"


def score_no_website_lead(lead):
    score = 0

    if not has_website(lead):
        score += 40

    if _safe_int((lead or {}).get("review_count"), 0) > 20:
        score += 20

    if _safe_float((lead or {}).get("rating"), 0.0) >= 4.0:
        score += 15

    category_context = " ".join(
        str((lead or {}).get(key) or "")
        for key in ("category", "niche", "description", "business_name")
    ).lower()
    if "restaurant" in category_context:
        score += 10

    if has_phone_contact(lead):
        score += 10

    return max(0, min(100, score))



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
        workflow_app = wf.compile()
        mem_client = chromadb.Client() if chromadb else None
        lf = Langfuse() if Langfuse else None
        try:
            if logfire and getattr(config, "LOGFIRE_API_KEY", None):
                logfire.init(api_key=config.LOGFIRE_API_KEY)
        except Exception:
            pass
        for event in workflow_app.stream({"messages": [("user", "status and next actions")] }):
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
    if args.serve:
        if not app or not uvicorn:
            raise RuntimeError("Web mode requires FastAPI and uvicorn to be importable.")
        print(f"Starting API server on port {config.FASTAPI_PORT}...")
        uvicorn.run(app, host="0.0.0.0", port=config.FASTAPI_PORT)
        return
    if args.signals:
        dm = DataManager()
        smtp_accounts = config.get_smtp_accounts()
        smtp_pool = build_smtp_pool(smtp_accounts)
        mailers = smtp_pool.mailers or [Mailer("", "", config.SMTP_SERVER, config.SMTP_PORT)]
        mailer = smtp_pool.peek_mailer() or mailers[0]
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
        def quick_observation(text, triggers=None):
            triggers = triggers or []
            tx = (text or "").lower()
            
            # Use triggers to generate specific observations
            if "no_ssl" in triggers:
                return "the site still uses HTTP instead of HTTPS"
            if "old_php" in triggers:
                return "the site appears to be running older PHP which might affect performance"
            if "old_jquery" in triggers:
                return "the site uses an older version of jQuery"
            if "missing_schema" in triggers:
                return "the site lacks structured data markup for better search visibility"
            if "slow_pagespeed" in triggers:
                return "the page load speed could be improved for better user experience"
            if "shopify_no_apple_pay" in triggers:
                return "the Shopify store doesn't seem to have Apple Pay enabled"
            if "wordpress_heavy_theme" in triggers:
                return "the WordPress site uses a heavy theme that might slow it down"
            if "no_google_pixel" in triggers:
                return "the site doesn't have Google Analytics tracking"
            if "no_fb_pixel" in triggers:
                return "the site lacks Facebook pixel for conversion tracking"
            if "no_mobile_viewport" in triggers:
                return "the site is missing a mobile viewport meta tag"
            if "large_page_size" in triggers:
                return "the page size is quite large which may affect loading speed"
            if "font_loading_issue" in triggers:
                return "font loading might be causing layout shifts"
            if "missing_alt_tags" in triggers:
                return "some images are missing alt tags for accessibility"
            
            # Fallback to text-based observations
            if "tel:" not in tx and "call" not in tx:
                return "the call option wasn't obvious on first view"
            if "contact" in tx and "book" not in tx and "schedule" not in tx:
                return "the booking step wasn't immediately clear"
            if "phone" in tx and "footer" in tx:
                return "the phone number seemed easy to miss"
            return "the next step wasn't obvious at first glance"
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
            if "<meta name=\"viewport\"" not in text.lower():
                triggers.append("no_mobile_viewport")
            if len(text) > 500000:  # Rough check for large pages
                triggers.append("large_page_size")
            if "font-awesome" in text.lower() and "font-display" not in text.lower():
                triggers.append("font_loading_issue")
            if "<img" in text and "alt=" not in text:
                triggers.append("missing_alt_tags")
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
                            smtp_pool.send_email(picked, subj, body, preferred_mailer=mailer)
                            dm.log_action(name, "email_sent", {"sequence_stage": "initial"})
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
                    "audit_issues": ";".join(t),
                    "website_signals": {},
                    "competitors": [],
                    "pagespeed_score": ps,
                    "opportunity_score": None,
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
                    # Build lead_data for advanced pipeline
                    lead_data = {
                        "business_name": name,
                        "industry": niche,
                        "city": location,
                        "website": u,
                        "audit_issues": t,
                        "pagespeed_score": ps,
                        "first_name": "there",
                        "description": "",
                        "reviews": [],
                        "competitors": [],
                        "rating": None,
                        "review_count": None,
                    }
                    # Try to get more data
                    try:
                        if yelp_api:
                            yelp_results = yelp_api.scrape(f"{name} {location}")
                            if yelp_results:
                                lead = yelp_results[0]
                                lead_data["rating"] = lead.get("rating")
                                lead_data["review_count"] = lead.get("review_count")
                                lead_data["reviews"] = [lead.get("description", "")] if lead.get("description") else []
                    except Exception:
                        pass
                    
                    result = run_pipeline(lead_data)
                    subj = result.get("subject", f"Quick note about {name}")
                    body = result.get("email", "")
                    if getattr(config, "DRY_RUN", False):
                        log("dry_send_preview", to=picked, subject=subj, body_preview=body[:200])
                        dm.record_email_event(name, "dry_preview", {"to": picked})
                    else:
                        smtp_pool.send_email(picked, subj, body, preferred_mailer=mailer)
                        dm.log_action(name, "email_sent", {"sequence_stage": "initial"})
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
                            obs = "the website could benefit from some optimization opportunities"
                            subj, body = llm_helper.generate_email_master(name, "business", "online", obs)
                            if getattr(config, "DRY_RUN", False):
                                log("dry_send_preview", to=em, subject=subj, body_preview=body[:200])
                                dm.record_email_event(name, "dry_preview", {"to": em})
                            else:
                                smtp_pool.send_email(em, subj, body, preferred_mailer=mailer)
                                dm.log_action(name, "email_sent", {"sequence_stage": "initial"})
            print("Signals session finished.")
        asyncio.run(run())
        return
    if args.dry_run:
        config.DRY_RUN = True
    dm = DataManager()
    smtp_accounts = config.get_smtp_accounts()
    smtp_pool = build_smtp_pool(smtp_accounts)
    mailers = list(smtp_pool.mailers)
    if not mailers:
        print("[SMTP] No SMTP accounts configured. Switching to DRY_RUN mode.")
        config.DRY_RUN = True
        mailers = [Mailer("", "", config.SMTP_SERVER, config.SMTP_PORT)]
        smtp_pool = None
    mailer = smtp_pool.peek_mailer() if smtp_pool else mailers[0]
    
    # Initialize Scrapers
    scraper = Scraper(headless=config.HEADLESS) 
    yelp_api = yelp_api_scraper.YelpApiScraper()
    osm = osm_scraper.OsmScraper()
    # apollo = apollo_scraper.ApolloScraper() # Removed
    
    cfg_issues = config.validate_config()
    if cfg_issues and not config.DRY_RUN:
        log("config_issues", issues=cfg_issues)
        config.DRY_RUN = True
    
    driver = scraper.get_driver()
    if not config.DRY_RUN:
        working_mailer = smtp_pool.get_working_mailer(test_login=True) if smtp_pool else None
        if not working_mailer:
            print("[SMTP] Falling back to DRY_RUN due to connection failure.")
            config.DRY_RUN = True
        else:
            mailer = working_mailer
    
    # 2. Daily Limit Check (DB Based)
    daily_count = dm.count_daily_actions()
    print(f"Daily actions so far: {daily_count}/{config.MAX_DAILY_ACTIONS}")
    
    # 3. Query Selection (Global Loop)
    if args.batch:
        print("\n--- BATCH MODE: Processing existing leads from database ---")
        import sqlite3
        conn = dm.get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM leads
            WHERE email IS NOT NULL
              AND email != ''
              AND COALESCE(sequence_stage, 'initial') = 'initial'
              AND COALESCE(status, 'scraped') NOT IN ('emailed', 'manual_queue', 'low_priority', 'no_contact', 'not_interested', 'bounced', 'appointment_booked', 'sale_closed', 'blacklisted', 'completed')
              AND (next_action_due IS NULL OR next_action_due <= datetime('now'))
            LIMIT ?
        """, (args.limit or 20,))
        leads_sorted_batch = [dict(row) for row in cur.fetchall()]
        conn.close()
        print(f"Found {len(leads_sorted_batch)} candidate leads in database.")
        
        # We simulate a single "batch" query loop
        queries = ["Batch Mode"]
        session_queries = ["Batch Mode"]
    elif args.query:
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
    
    emails_sent_in_batch = 0
    for query in session_queries:
        if daily_count >= config.MAX_DAILY_ACTIONS:
            print("Daily limit reached (start of loop).")
            break
            
        print(f"\n--- Campaign: {query} ---")
        
        if args.batch:
            leads_raw = leads_sorted_batch
        else:
            # Parallel Scraping
            leads_raw = run_parallel_scraping(query, scraper, driver, yelp_api, osm)
        
        # Fallback to Bing/YP if ABSOLUTELY nothing found (Sequential fallback still useful here as last resort)
        if len(leads_raw) == 0 and not args.batch:
             print("All primary scrapers failed. Trying legacy fallbacks...")
             # ... (Keep legacy fallback logic if desired, or assume parallel covers it)
        
        # 4. Priority Sorting: No-website businesses first
        if config.PRIORITIZE_NO_WEBSITE and not args.batch:
            leads_no_site = [l for l in leads_raw if classify_lead(l) == "no_website"]
            leads_with_site = [l for l in leads_raw if classify_lead(l) == "has_website"]
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
            website = _normalized_text(lead_info.get('website'))
            lead_info['website'] = website
            lead_info['email'] = _normalized_text(lead_info.get('email'))
            lead_info['phone'] = _normalized_text(lead_info.get('phone'))
            # If Yelp API provided only Yelp URL, try to resolve business website
            if not website and lead_info.get('yelp_url'):
                try:
                    from yelp_scraper import extract_business_website
                    w = extract_business_website(lead_info.get('yelp_url'))
                    if w:
                        website = _normalized_text(w)
                        lead_info['website'] = website
                except Exception:
                    pass
            lead_type = classify_lead({"website": website})
            rating = _safe_float(lead_info.get('rating', 0), 0.0)
            reviews = _safe_int(lead_info.get('review_count', 0), 0)
            description = lead_info.get('description')
            sample_reviews = lead_info.get('sample_reviews')
            
            # Check DB existence (Skip if in batch mode)
            if not args.batch and dm.lead_exists(name, website):
                continue
            
            # --- SAFETY THROTTLES (from send_10_emails.py) ---
            email = _normalized_text(lead_info.get('email'))
            if email:
                email_domain = email.split("@")[-1].lower() if "@" in email else ""
                # 1. Blacklist Check
                if email_domain in config.BLACKLISTED_DOMAINS or email.lower() in config.BLACKLISTED_EMAILS:
                    print(f"  -> Skipping blacklisted lead: {name} <{email}>")
                    continue
                
                # 2. Domain Throttle
                if email_domain and dm.count_daily_actions_for_domain(email_domain) >= config.MAX_DOMAIN_SENDS_PER_DAY:
                    print(f"  -> Skipping {name}: reached daily domain throttle for {email_domain}.")
                    continue

            # 3. City Throttle
            city = lead_info.get('city')
            if city and dm.count_daily_actions_for_city(city) >= config.MAX_CITY_SENDS_PER_DAY:
                print(f"  -> Skipping {name}: reached daily city throttle for {city}.")
                continue
            # ------------------------------------------------
            
            # Strategy Filter (Rating-based, reviews optional)
            if rating < config.MIN_RATING:
                continue
                
            print(f"\nAnalyzing: {name} (Web: {website} | {rating}* ({reviews} reviews))")
            
            # Duplicate Detection: Check if website belongs to parent company
            parent_company_id = None
            normalized_website = canonicalize_website(website) if website else None
            if normalized_website and dm.is_parent_company(normalized_website):
                print(f"  -> Duplicate website detected: {website}")
                parent_company_id = dm.get_parent_company_id(normalized_website)
                dm.increment_parent_company_count(normalized_website)
                # Save lead but don't email (parent already contacted)
                lead_info['parent_company_id'] = parent_company_id
                lead_info['city'] = query.split(" near ")[-1]
                lead_info['niche'] = query.split(" near ")[0]
                dm.save_lead(lead_info)
                print(f"  -> Saved as duplicate, skipping email")
                continue
            
            strategy = "audit"
            audit_issues = []
            email = lead_info.get('email')
            first_name = None
            website_status = None
            screenshot_path = None
            web_signals = {}
            pagespeed_score = None
            opportunity_score = None
            
            # Branch A: No Website
            if lead_type == "no_website":
                strategy = "no_website"
                opportunity_score = score_no_website_lead(lead_info)
                audit_issues = [f"No website opportunity score: {opportunity_score}/100."]
                print(
                    f"  -> Strategy: NO WEBSITE (Opportunity Pitch) "
                    f"[score={opportunity_score}/{config.NO_WEBSITE_MIN_SCORE}]"
                )
                if opportunity_score < config.NO_WEBSITE_MIN_SCORE:
                    lead_info['audit_issues'] = "; ".join(audit_issues)
                    lead_info['strategy'] = strategy
                    lead_info['city'] = query.split(" near ")[-1]
                    lead_info['niche'] = query.split(" near ")[0]
                    lead_info['description'] = description
                    lead_info['status'] = "low_priority"
                    dm.save_lead(lead_info)
                    dm.record_email_event(
                        name,
                        "no_website_scored_out",
                        {
                            "lead_type": lead_type,
                            "opportunity_score": opportunity_score,
                            "min_score": config.NO_WEBSITE_MIN_SCORE,
                        },
                    )
                    print("  -> Skipping: no-website opportunity score below threshold.")
                    continue
            # Branch B: Website
            else:
                strategy = "audit"
                print("  -> Strategy: AUDIT (Redesign Pitch)")
                
                # BATCH MODE BYPASS: Reuse existing audit if available
                if args.batch and lead_info.get('audit_issues'):
                    print("  -> Using existing audit data from database.")
                    audit_issues = [i.strip() for i in str(lead_info.get('audit_issues')).split(";") if i.strip()]
                    web_signals = lead_info.get('website_signals') or {}
                    if isinstance(web_signals, str):
                        try: web_signals = json.loads(web_signals)
                        except: web_signals = {}
                    email_site = lead_info.get('email')
                else:
                    # Use scraper for basic info
                    try:
                        email_site, audit_issues, web_signals = scraper.process_website(website)
                    except Exception as e:
                        print(f"  -> Error processing website {website}: {e}")
                        continue

                email = email or email_site
                
                # TECH FILTERING (New)
                if args.tech:
                    found_tech = web_signals.get("tech", [])
                    print(f"  -> Tech found: {found_tech}")
                    required_tech = args.tech.lower()
                    if not any(required_tech in t.lower() for t in found_tech):
                         print(f"  -> Skipping: Tech '{args.tech}' not found.")
                         continue
                
                # ENHANCED AUDIT (PageSpeed + Screenshot)
                screenshot_path = None
                if not (args.batch and lead_info.get('pagespeed_score')) and getattr(config, "PAGESPEED_API_KEY", None):
                    try:
                        import asyncio
                        # Create new event loop for async call if needed, or run
                        pagespeed_score, screenshot_path = asyncio.run(pagespeed(website))
                        if pagespeed_score is not None:
                            if pagespeed_score < 0.5:
                                audit_issues.append(f"Google PageSpeed score is poor ({int(pagespeed_score * 100)}/100).")
                                strategy = "broken_site" # refined strategy name
                            print(f"  -> PageSpeed Score: {pagespeed_score}")
                    except Exception as e:
                        print(f"  -> PageSpeed Error: {e}")
                elif args.batch and lead_info.get('pagespeed_score'):
                    pagespeed_score = lead_info.get('pagespeed_score')
                    print(f"  -> Using existing PageSpeed Score: {pagespeed_score}")

                # FREEDOM SEARCH (Find CEO)
                # Combine site email with finding decision maker
                # Use FreedomSearch (reusing driver)
                fs = FreedomSearch(driver) 
                # Parse domain
                from urllib.parse import urlparse
                domain = urlparse(website).netloc.replace("www.", "")
                
                ceo_name = None
                email_person = None
                
                if not (args.batch and lead_info.get('email')) and (args.audit or not email_site):
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
                    
                email = email or email_person or email_site
                
                # Register parent
                if normalized_website and not dm.is_parent_company(normalized_website):
                    parent_company_id = dm.create_parent_company(normalized_website, name)
                    lead_info['parent_company_id'] = parent_company_id

                if not description:
                    description = (
                        web_signals.get("headline")
                        or web_signals.get("homepage_summary")
                        or web_signals.get("meta_description")
                    )

            lead_info['audit_issues'] = "; ".join(audit_issues or [])
            lead_info['strategy'] = strategy
            lead_info['website_signals'] = web_signals
            lead_info['service_offerings'] = ", ".join([str(item).strip() for item in web_signals.get('services', [])[:4] if str(item).strip()])
            lead_info['homepage_cta_quality'] = (
                "Homepage CTA appears unclear or buried." if web_signals.get('cta_visibility') == 'unclear' else
                "Homepage CTA appears visible and direct." if web_signals.get('cta_visibility') else None
            )
            lead_info['review_sentiment'] = (
                f"{rating}-star average from {reviews} reviews" if rating and reviews else (
                    f"{rating}-star average" if rating else (f"{reviews} reviews" if reviews else None)
                )
            )
            lead_info['review_excerpt'] = description or lead_info.get('sample_reviews') or None
            lead_info['local_market_signal'] = (
                f"In {lead_info.get('city') or 'your area'}, nearby businesses are often chosen by whoever makes the first message easiest to act on."
            )
            lead_info['competitor_references'] = None
            lead_info['pagespeed_score'] = pagespeed_score
            lead_info['opportunity_score'] = opportunity_score
            lead_info['competitors'] = lead_info.get('competitors') or []
            lead_info['service_pages'] = ", ".join(web_signals.get('service_pages', [])[:6]) if web_signals else None
            lead_info['pricing_mention'] = web_signals.get('pricing_mention')
            lead_info['booking_widget'] = web_signals.get('booking_widget')
            lead_info['operating_hours'] = web_signals.get('operating_hours')
            lead_info['location_count'] = web_signals.get('location_count')
            lead_info['staff_count'] = web_signals.get('staff_count')
            lead_info['business_size'] = web_signals.get('business_size')
            lead_info['google_business_profile_status'] = web_signals.get('google_business_profile_status')
            lead_info['review_velocity'] = web_signals.get('review_velocity')
            lead_info['keyword_usage'] = ", ".join(web_signals.get('keyword_usage', [])[:8]) if web_signals else None
            lead_info['secondary_emails'] = ", ".join(web_signals.get('secondary_emails', [])[:3]) if web_signals else None
            lead_info['phone_numbers'] = ", ".join(web_signals.get('phone_numbers', [])[:3]) if web_signals else None
            lead_info['whatsapp_links'] = ", ".join(web_signals.get('whatsapp_links', [])[:3]) if web_signals else None
            lead_info['service_offerings'] = ", ".join([str(item).strip() for item in web_signals.get('services', [])[:4] if str(item).strip()])
            lead_info['homepage_cta_quality'] = (
                "Homepage CTA appears unclear or buried." if web_signals.get('cta_visibility') == 'unclear' else
                "Homepage CTA appears visible and direct." if web_signals.get('cta_visibility') else None
            )
            lead_info['spf_status'] = None
            lead_info['dmarc_status'] = None
            lead_info['email_quality'] = None

            if not email:
                if lead_type == "no_website":
                    lead_info['audit_issues'] = "; ".join(audit_issues or [])
                    lead_info['strategy'] = strategy
                    lead_info['city'] = query.split(" near ")[-1]
                    lead_info['niche'] = query.split(" near ")[0]
                    lead_info['description'] = description
                    if has_phone_contact(lead_info) and getattr(config, "QUEUE_PHONE_ONLY_LEADS", True):
                        lead_info['status'] = "manual_queue"
                        dm.save_lead(lead_info)
                        dm.record_email_event(
                            name,
                            "manual_outreach_candidate",
                            {
                                "lead_type": lead_type,
                                "channel": "phone",
                                "phone": lead_info.get("phone"),
                                "reason": "no_email_for_no_website_lead",
                                "opportunity_score": opportunity_score,
                            },
                        )
                        print(
                            f"  -> No email found. Queued for manual phone/WhatsApp follow-up "
                            f"({lead_info.get('phone')})."
                        )
                    else:
                        lead_info['status'] = "no_contact"
                        dm.save_lead(lead_info)
                        dm.record_email_event(
                            name,
                            "no_contact_method",
                            {
                                "lead_type": lead_type,
                                "reason": "no_email_and_no_phone_for_no_website_lead",
                                "opportunity_score": opportunity_score,
                            },
                        )
                        print("  -> Skipping: no email and no phone for no-website lead.")
                    continue
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
                    best_validation = None
                    for cand in candidates:
                        try:
                            validation_mailer = smtp_pool.peek_mailer() if smtp_pool else mailer
                            validation = validation_mailer.assess_email(
                                cand,
                                smtp_probe=False,
                                allow_risky=True,
                                check_catch_all=False,
                            )
                        except Exception:
                            validation = {"can_send": False, "score": 0, "status": "INVALID"}
                        if validation.get("can_send"):
                            fallback_email = cand
                            print(
                                f"  -> Using validated fallback email: {fallback_email} "
                                f"(score={validation.get('score')})"
                            )
                            break
                        if not best_validation or validation.get("score", 0) > best_validation.get("score", 0):
                            best_validation = dict(validation)
                            best_validation["email"] = cand
                    if not fallback_email and best_validation and best_validation.get("score", 0) >= 50:
                        print(
                            f"  -> Only risky fallback emails found for {name}; "
                            f"best candidate {best_validation.get('email')} scored {best_validation.get('score')}."
                        )
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
            if isinstance(audit_issues, str):
                lead_info['audit_issues'] = audit_issues
            else:
                lead_info['audit_issues'] = "; ".join(audit_issues or [])
            lead_info['strategy'] = strategy
            lead_info['city'] = query.split(" near ")[-1]
            lead_info['niche'] = query.split(" near ")[0]
            lead_info['description'] = description
            
            # Save to DB
            dm.save_lead(lead_info)
            if lead_type == "no_website":
                dm.record_email_event(
                    name,
                    "no_website_scored",
                    {
                        "lead_type": lead_type,
                        "opportunity_score": opportunity_score,
                        "email_available": bool(email),
                        "phone_available": has_phone_contact(lead_info),
                    },
                )
            
            # 6. Email Generation (with personalization)
            time.sleep(random.uniform(1.2, 2.8))
            
            # Parse reviews from JSON
            import json
            reviews_list = []
            if sample_reviews:
                if isinstance(sample_reviews, str):
                    try:
                        reviews_list = json.loads(sample_reviews)
                    except json.JSONDecodeError:
                        reviews_list = [sample_reviews]
                elif isinstance(sample_reviews, (list, tuple)):
                    reviews_list = list(sample_reviews)

            peer_competitors = []
            for peer in leads_sorted:
                peer_name = peer.get("business_name")
                if not peer_name or peer_name == name:
                    continue
                peer_competitors.append({
                    "business_name": peer_name,
                    "website": peer.get("website"),
                    "rating": peer.get("rating"),
                })
                if len(peer_competitors) >= 3:
                    break

            competitor_references = ", ".join([peer.get("business_name") for peer in peer_competitors if peer.get("business_name")])
            lead_info['competitors'] = peer_competitors
            lead_info['competitor_references'] = competitor_references
            if peer_competitors:
                dm.save_lead(lead_info)

            recent_personas = dm.get_recent_personas(name)
            past_outcomes = dm.get_recent_outcomes(name)
            review_snippet = reviews_list[0] if reviews_list else ""
            review_sentiment = lead_info.get('review_sentiment') or (
                f"{rating}-star average from {reviews} reviews" if rating and reviews else (
                    f"{rating}-star average" if rating else (f"{reviews} reviews" if reviews else "")
                )
            )
            website_issue = audit_issues[0] if audit_issues else ""
            good_fit_reason = (
                f"Because {name} already has local momentum in {lead_info.get('city') or 'your area'}, this outreach can help turn more Maps interest into booked work."
                if lead_info.get('city') else f"Because {name} already has local momentum, this outreach can help turn more Maps interest into booked work."
            )
            unique_value = (
                f"Helping {name} convert Google Maps visits into booked jobs with one simple website or listing improvement."
                if website else f"Helping {name} capture local demand even without a website by making the first contact path clearer and faster."
            )
            lead_context = {
                "business_name": name,
                "first_name": first_name,
                "industry": lead_info["niche"],
                "city": lead_info["city"],
                "lead_type": lead_type,
                "website": website,
                "email": email,
                "phone": lead_info.get("phone"),
                "rating": rating,
                "review_count": reviews,
                "description": description,
                "audit_issues": audit_issues,
                "reviews": reviews_list,
                "review_snippet": review_snippet,
                "review_sentiment": review_sentiment,
                "service_offerings": lead_info.get("service_offerings"),
                "review_excerpt": lead_info.get("review_excerpt") or review_snippet,
                "local_market_signal": lead_info.get("local_market_signal"),
                "competitor_references": lead_info.get("competitor_references"),
                "homepage_cta_quality": lead_info.get("homepage_cta_quality"),
                "website_issue": website_issue,
                "good_fit_reason": good_fit_reason,
                "unique_value": unique_value,
                "competitors": peer_competitors,
                "website_signals": web_signals,
                "pagespeed_score": pagespeed_score,
                "opportunity_score": opportunity_score,
                "open_count": lead_info.get("open_count") or 0,
                "last_opened_at": lead_info.get("last_opened_at"),
                "past_outcomes": past_outcomes,
                "persona_history": recent_personas,
            }
            dm.record_email_event(name, "prompt_payload", {"prompt_payload": lead_context})
            if lead_type == "no_website":
                strategy_event = "no_website_prompt_strategy_generated"
                retry_event = "no_website_prompt_quality_retry"
            else:
                strategy_event = "website_prompt_strategy_generated"
                retry_event = "website_prompt_quality_retry"

            outreach_result = None
            for attempt in range(3):
                try:
                    outreach_result = llm_helper.generate_maps_cold_email(lead_context)
                    break
                except Exception as e:
                    if attempt < 2:
                        log("llm_generation_retry", name=name, attempt=attempt + 1, error=str(e))
                        continue
                    log("llm_generation_failed", name=name, error=str(e))
                    dm.record_email_event(name, "llm_generation_failed", {"error": str(e), "attempts": 3})
                    outreach_result = None
            if outreach_result is None:
                continue

            subject = outreach_result.get("subject") or f"Quick note about {name}"
            body = outreach_result.get("email") or ""
            quality_result = llm_helper.evaluate_structured_email_quality(body, lead_context, lead_type == "has_website", persona_name=outreach_result.get("persona"))
            if quality_result.get("issues"):
                dm.record_email_event(name, "llm_quality_warning", {
                    "provider": outreach_result.get("provider"),
                    "persona": outreach_result.get("persona"),
                    "score": quality_result.get("score"),
                    "issues": quality_result.get("issues"),
                })

            # 4. Persona Throttle (from send_10_emails.py)
            persona = outreach_result.get("persona")
            if persona and dm.count_daily_actions_for_persona(persona) >= config.MAX_PERSONA_SENDS_PER_DAY:
                print(f"  -> Skipping {name}: reached daily persona throttle for {persona}.")
                continue
            # ----------------------------------------------

            dm.record_email_event(name, "persona_selected", {
                "provider": outreach_result.get("provider"),
                "persona": outreach_result.get("persona"),
                "lead_type": lead_type,
                "hook_type": outreach_result.get("hook_type"),
            })
            dm.record_email_event(name, "email_generated", {
                "provider": outreach_result.get("provider"),
                "persona": outreach_result.get("persona"),
                "subject": subject,
                "lead_type": lead_type,
                "hook_type": outreach_result.get("hook_type"),
                "analysis_provider": outreach_result.get("analysis_provider"),
            })
            dm.record_email_event(
                name,
                strategy_event,
                {
                    "lead_type": lead_type,
                    "opportunity_score": opportunity_score,
                    "persona": outreach_result.get("persona"),
                    "hook_type": outreach_result.get("hook_type"),
                    "observations": outreach_result.get("observations"),
                    "problems": outreach_result.get("problems"),
                    "strategy": outreach_result.get("strategy"),
                    "insight": outreach_result.get("insight"),
                    "analysis_provider": outreach_result.get("analysis_provider"),
                    "provider": outreach_result.get("provider"),
                },
            )
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
                dm.record_email_event(name, "dry_preview", {"to": email, "subject": subject})
                sent = True # Simulate success
            else:
                if not in_window:
                    log("email_skipped_window", to=email)
                    dm.record_email_event(name, "skipped_window", {"to": email})
                    continue
                
                preferred_mailer = smtp_pool.peek_mailer() if smtp_pool else mailer
                allow_risky = getattr(config, "ALLOW_RISKY_EMAILS", False)
                validation_result = preferred_mailer.assess_email(
                    email,
                    smtp_probe=False,
                    allow_risky=allow_risky,
                    check_catch_all=False,
                )
                checks = validation_result.get("checks", {})
                lead_info["spf_status"] = "valid" if checks.get("spf_valid") else "invalid" if checks.get("spf_valid") is False else None
                lead_info["dmarc_status"] = validation_result.get("dmarc_policy")
                lead_info["email_quality"] = validation_result.get("classification") or validation_result.get("status")
                dm.save_lead(lead_info)
                log(
                    "email_validation_result",
                    to=email,
                    status=validation_result.get("status"),
                    score=validation_result.get("score"),
                    smtp=checks.get("smtp_valid", checks.get("smtp_mailbox_exists")),
                    spf=checks.get("spf_valid"),
                    dmarc=validation_result.get("dmarc_policy"),
                    catch_all=checks.get("catch_all"),
                    disposable=checks.get("disposable", checks.get("is_disposable")),
                )
                dm.record_email_event(
                    name,
                    "validation_result",
                    {
                        "to": email,
                        "status": validation_result.get("status"),
                        "score": validation_result.get("score"),
                        "checks": checks,
                        "reasons": validation_result.get("reasons"),
                    },
                )

                if validation_result.get("can_send"):
                    if smtp_pool:
                        sent = smtp_pool.send_email(
                            email,
                            subject,
                            body,
                            attachment_paths=[screenshot_path] if screenshot_path else None,
                            validation_result=validation_result,
                            preferred_mailer=preferred_mailer,
                            retries_per_account=1,
                        )
                    else:
                        sent = preferred_mailer.send_email(
                            email,
                            subject,
                            body,
                            attachment_paths=[screenshot_path] if screenshot_path else None,
                            validation_result=validation_result,
                        )
                else:
                    print(
                        f"[SMTP] Skipping {email} - Validation failed "
                        f"(status={validation_result.get('status')}, score={validation_result.get('score')}, "
                        f"reasons={validation_result.get('reasons')})."
                    )
                    log(
                        "email_skipped_validation",
                        to=email,
                        status=validation_result.get("status"),
                        score=validation_result.get("score"),
                    )
                    sent = False
                
                from_mailer = smtp_pool.last_used_mailer if smtp_pool and smtp_pool.last_used_mailer else preferred_mailer
                log("email_sent_result", to=email, sent=bool(sent), from_email=from_mailer.email)
                dm.record_email_event(name, "email_send_attempt", {
                    "to": email,
                    "provider": outreach_result.get("provider"),
                    "persona": outreach_result.get("persona"),
                    "hook_type": outreach_result.get("hook_type"),
                    "sent": bool(sent),
                })
                dm.record_email_event(name, "sent" if sent else "failed", {
                    "to": email,
                    "provider": outreach_result.get("provider"),
                    "persona": outreach_result.get("persona"),
                    "hook_type": outreach_result.get("hook_type"),
                })
                try:
                    dm.record_training_example(
                        name,
                        subject,
                        body,
                        quality_result.get("score"),
                        quality_result.get("tone"),
                        "sent" if sent else "failed",
                        persona=outreach_result.get("persona"),
                        strategy_text=outreach_result.get("strategy"),
                        insight=outreach_result.get("insight"),
                    )
                except Exception:
                    pass
            
            if sent:
                 if config.DRY_RUN:
                     print(f"Dry run preview generated for {name}.")
                     continue
                 dm.log_action(name, "email_sent", {"sequence_stage": "initial"})
                 
                 # Human-Like Jitter
                 if not getattr(config, "SKIP_JITTER", False):
                     wait_time = random.randint(120, 360)
                     print(f"Email sent to {name}. Waiting {wait_time}s...")
                     time.sleep(wait_time)
                 else:
                     print(f"Email sent to {name}. Skipping jitter per config.")

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
                    event_meta = ev.get("meta") or {}
                    last_email_meta = dm.get_last_event_meta(business, ["email_generated", "sent", "email_send_attempt"])
                    if last_email_meta and not event_meta.get("hook_type"):
                        hook_type = last_email_meta.get("hook_type")
                        if hook_type:
                            event_meta["hook_type"] = hook_type
                    dm.record_email_event(business, ev.get("type"), event_meta)
                    if ev.get("type") == "opened":
                        dm.log_action(business, "opened", event_meta)
                    elif ev.get("type") in ("reply", "appointment_booked", "sale_closed", "bounce"):
                        dm.log_action(business, ev.get("type"), event_meta)
                        if ev.get("type") in ("reply", "appointment_booked", "sale_closed"):
                            dm.capture_successful_outreach(business)
                        if ev.get("type") == "bounce" and smtp_pool and smtp_pool.last_used_mailer:
                            smtp_pool.mark_account_bad(smtp_pool.last_used_mailer, reason="imap_bounce")
                    log("email_outcome_recorded", type=ev.get("type"), email=email_addr, business=business)
                    if ev.get("type") in ("reply", "appointment_booked", "sale_closed", "bounce"):
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
