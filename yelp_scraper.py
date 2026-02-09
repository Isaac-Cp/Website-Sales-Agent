import urllib.parse
import time
import random
import httpx
from bs4 import BeautifulSoup
import random

def scrape_yelp(niche, city, max_leads=15):
    """
    Scrapes Yelp HTML search results for a given niche and city.
    Returns a list of dicts in the same format as Maps leads:
    {business_name, website, phone, rating, review_count, description, sample_reviews, source}
    """
    leads = []
    try:
        q_desc = urllib.parse.quote(niche)
        q_loc = urllib.parse.quote(city)
        url = f"https://www.yelp.com/search?find_desc={q_desc}&find_loc={q_loc}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        with httpx.Client(http2=True, follow_redirects=True, timeout=15.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                return leads
            soup = BeautifulSoup(resp.text, "html.parser")

            # Find business result links; Yelp uses /biz/ paths
            biz_links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/biz/"):
                    name = (a.text or "").strip()
                    if name and name.lower() != "more info":
                        biz_links.append((f"https://www.yelp.com{href}", name))

            # Deduplicate by URL
            seen = set()
            unique_links = []
            for href, name in biz_links:
                if href not in seen:
                    unique_links.append((href, name))
                    seen.add(href)

            for href, name in unique_links[:max_leads]:
                website = None
                rating = 0.0
                review_count = 0
                description = None
                sample_reviews = []

                try:
                    detail = client.get(href, headers=headers)
                    if detail.status_code != 200:
                        continue
                    dsoup = BeautifulSoup(detail.text, "html.parser")

                    # Rating: aria-label like "4.5 star rating"
                    try:
                        star = dsoup.find("div", attrs={"aria-label": True})
                        if star and "star rating" in star.get("aria-label", "").lower():
                            import re
                            m = re.search(r"(\d+(?:\.\d+)?)", star.get("aria-label"))
                            if m:
                                rating = float(m.group(1))
                    except:
                        pass

                    # Review count: look for strings like "123 reviews"
                    try:
                        import re
                        text = dsoup.get_text(" ")
                        m = re.search(r"(\d{1,3}(?:,\d{3})*|\d+)\s+reviews?", text.lower())
                        if m:
                            review_count = int(m.group(1).replace(",", ""))
                    except:
                        pass

                    # Website link: look for "Business website" section
                    try:
                        for a in dsoup.find_all("a", href=True):
                            ah = a.get("href", "")
                            txt = (a.text or "").strip().lower()
                            if ah.startswith("http") and "yelp" not in ah:
                                # Heuristic: first external link likely the business site
                                website = ah
                                break
                    except:
                        pass

                    # Description/category snippet
                    try:
                        # Often present near the name header or in meta
                        h1 = dsoup.find("h1")
                        if h1:
                            # Next sibling paragraphs sometimes include short descriptions
                            p = h1.find_next("p")
                            if p and len(p.text.strip()) > 0:
                                description = p.text.strip()
                    except:
                        pass

                    # Sample reviews: capture a few short review texts
                    try:
                        review_blocks = dsoup.select("p[class*='comment'], p[class*='raw__']")
                        for rb in review_blocks[:4]:
                            txt = rb.get_text(" ").strip()
                            if 20 < len(txt) < 400:
                                sample_reviews.append(txt)
                    except:
                        pass

                    leads.append({
                        "business_name": name,
                        "website": website,
                        "phone": "N/A",
                        "rating": rating,
                        "review_count": review_count,
                        "description": description,
                        "sample_reviews": None if not sample_reviews else __import__("json").dumps(sample_reviews),
                        "source": "yelp"
                    })
                    time.sleep(random.uniform(0.4, 1.1))
                except Exception:
                    continue

    except Exception:
        pass

    return leads

def extract_business_website(yelp_url):
    try:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        ]
        headers = {"User-Agent": random.choice(user_agents)}
        with httpx.Client(http2=True, follow_redirects=True, timeout=12.0) as client:
            r = client.get(yelp_url, headers=headers)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if href.startswith("http") and "yelp.com" not in href:
                return href
    except Exception:
        return None
    return None
