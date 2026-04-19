import httpx
from bs4 import BeautifulSoup
import re
import sqlite3
import time
from urllib.parse import urlparse, urljoin

def get_email_from_text(text):
    if not text: return None
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if match:
        return match.group(0)
    return None

def crawl_site(url):
    if not url.startswith("http"):
        url = "http://" + url
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0"}
    
    try:
        print(f"  Crawling {url}...")
        with httpx.Client(follow_redirects=True, timeout=10.0, verify=False) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200: return None
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # 1. Check homepage
            email = get_email_from_text(resp.text)
            if email: return email
            
            # 2. Check common pages
            links = soup.find_all("a", href=True)
            pages_to_check = []
            for link in links:
                href = link['href'].lower()
                if any(k in href for k in ["contact", "about", "team", "legal", "impressum", "contact-us"]):
                    full_url = urljoin(url, link['href'])
                    if full_url not in pages_to_check:
                        pages_to_check.append(full_url)
            
            for page in pages_to_check[:5]: # Limit to 5 subpages
                print(f"    Checking {page}...")
                try:
                    r = client.get(page, headers=headers)
                    if r.status_code == 200:
                        email = get_email_from_text(r.text)
                        if email: return email
                except:
                    continue
                    
    except Exception as e:
        print(f"    Error: {e}")
    
    return None

def main():
    conn = sqlite3.connect('leads.db')
    cur = conn.cursor()
    cur.execute("SELECT id, business_name, website FROM leads WHERE email IS NULL AND website IS NOT NULL AND website != '' LIMIT 10")
    leads = cur.fetchall()
    conn.close()
    
    print(f"Found {len(leads)} leads to check.")
    
    found_count = 0
    for lid, name, website in leads:
        print(f"Processing {name}...")
        email = crawl_site(website)
        if email:
            print(f"  SUCCESS: Found {email}")
            conn = sqlite3.connect('leads.db')
            conn.execute("UPDATE leads SET email = ?, status = 'scraped' WHERE id = ?", (email, lid))
            conn.commit()
            conn.close()
            found_count += 1
        else:
            print("  FAILED: No email found.")
        time.sleep(1)
        if found_count >= 5: break # find 5 more to be safe

if __name__ == "__main__":
    main()
