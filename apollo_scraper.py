try:
    import httpx as _httpx
except Exception:
    _httpx = None
import config

class ApolloScraper:
    def __init__(self, api_key=None):
        self.api_key = api_key or config.APOLLO_API_KEY
        self.base_url = "https://api.apollo.io/api/v1"

    def scrape(self, query, limit=15):
        if not self.api_key:
            print("[Apollo] Skipped: No API Key provided.")
            return []
            
        leads = []
        try:
            niche = query.split(" near ")[0]
            location = query.split(" near ")[-1]
            print(f"[Apollo] Searching organizations for '{niche}' in '{location}'...")
            url = f"{self.base_url}/organizations/search"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": self.api_key
            }
            payload = {
                "q_keywords": niche,
                "locations": [location],
                "page": 1,
                "per_page": max(1, min(100, limit))
            }
            if _httpx:
                with _httpx.Client(timeout=20) as client:
                    r = client.post(url, json=payload, headers=headers)
            else:
                import requests as _requests
                r = _requests.post(url, json=payload, headers=headers, timeout=20)
            if r.status_code != 200:
                print(f"[Apollo] HTTP {r.status_code}: {r.text[:200]}")
                return []
            data = r.json()
            orgs = data.get("organizations") or data.get("organizations_list") or []
            for o in orgs:
                name = o.get("name")
                website = o.get("website_url") or o.get("website") or o.get("domain")
                if website and not website.startswith("http"):
                    website = f"http://{website}"
                phone_raw = o.get("primary_phone") or o.get("phone")
                phone = None
                try:
                    if isinstance(phone_raw, dict):
                        phone = phone_raw.get("phone_number") or phone_raw.get("display") or None
                    elif isinstance(phone_raw, (list, tuple)):
                        phone = phone_raw[0] if phone_raw else None
                    else:
                        phone = phone_raw
                except Exception:
                    phone = None
                city = o.get("city") or location
                description = o.get("industry") or o.get("headline")
                lead = {
                    "business_name": name or "Unknown",
                    "website": website,
                    "phone": phone or "N/A",
                    "rating": 0.0,
                    "review_count": 0,
                    "description": description,
                    "sample_reviews": None,
                    "source": "apollo",
                    "city": city
                }
                leads.append(lead)
                if len(leads) >= limit:
                    break
            
        except Exception as e:
            print(f"[Apollo] Error: {e}")
            
        return leads
