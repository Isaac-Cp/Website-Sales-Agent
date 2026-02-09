
import time
import re
import dns.resolver
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper import Scraper

class FreedomSearch:
    def __init__(self, driver=None):
        """
        Initialize with an existing driver or create a new one using Scraper class.
        """
        self.driver = driver
        self.own_driver = False
        if not self.driver:
            self.scraper = Scraper()
            self.driver = self.scraper.get_driver()
            self.own_driver = True

    def scrape_team_page(self, base_url):
        """
        Navigates to About/Team pages and scrapes names/emails.
        """
        driver = self.driver
        found_contacts = []
        
        try:
            if not base_url.startswith("http"):
                base_url = "http://" + base_url
                
            driver.get(base_url)
            time.sleep(3)
            
            # Find "About" or "Team" links
            target_links = []
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    text = link.text.lower()
                    href = link.get_attribute("href")
                    if href and ("about" in text or "team" in text or "contact" in text or "over-ons" in text):
                        target_links.append(href)
            except:
                pass
                
            # Deduplicate
            target_links = list(set(target_links))[:3] # Limit to 3 pages
            
            pages_to_scrape = [base_url] + target_links
            
            for url in pages_to_scrape:
                try:
                    if url != driver.current_url:
                        driver.get(url)
                        time.sleep(2)
                        
                    # Scrape Emails (Simple Regex)
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", page_text)
                    for em in emails:
                        if em not in [c['email'] for c in found_contacts]:
                             found_contacts.append({"name": "Unknown", "email": em, "source": "site_scrape"})

                    # Try to find names near titles like "CEO", "Founder"
                    # This is hard with regex, maybe look for specific elements?
                    # For now, just getting emails is a big win.
                    
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Team scrape error: {e}")
            
        return found_contacts


    def search_google(self, query):
        """
        Scrapes Google Search Results for a query.
        Returns a list of dicts with {title, link, snippet}.
        """
        driver = self.driver
        print(f"[FreedomSearch] Googling: {query}")
        try:
            driver.get("https://www.google.com")
            
            # Handle cookie consent (Generic common selectors)
            try:
                WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all') or contains(., 'Alles accepteren') or contains(., 'Tout accepter')]"))
                ).click()
            except:
                pass
                
            # Find search box
            try:
                search_box = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "q"))
                )
                search_box.clear()
                search_box.send_keys(query)
                search_box.send_keys(Keys.ENTER)
            except Exception as e:
                print(f"[FreedomSearch] Search box error: {e}")
                return []
                
            # Wait for results
            time.sleep(3)
            
            results = []
            # Parse results (div.g is the standard container for organic results)
            elements = driver.find_elements(By.CSS_SELECTOR, "div.g")
            
            for el in elements:
                try:
                    title_el = el.find_element(By.TAG_NAME, "h3")
                    link_el = el.find_element(By.TAG_NAME, "a")
                    
                    link = link_el.get_attribute("href")
                    title = title_el.text
                    
                    if link and title:
                        results.append({
                            "title": title,
                            "link": link
                        })
                except:
                    continue
            
            return results
            
        except Exception as e:
            print(f"[FreedomSearch] Error: {e}")
            return []

    def find_ceo(self, company, city=None):
        """
        Finds the CEO/Founder name and LinkedIn profile for a company.
        """
        # Query variations
        queries = [
            f"CEO {company} {city or ''} site:linkedin.com/in",
            f"Founder {company} {city or ''} site:linkedin.com/in",
            f"Owner {company} {city or ''} site:linkedin.com/in"
        ]
        
        for q in queries:
            results = self.search_google(q)
            for r in results:
                title = r['title']
                # Patterns: "Name - CEO - Company", "Name | Founder | Company", "Name - Owner"
                # We prioritize the name at the start.
                
                # Split by separators
                parts = re.split(r" [-|] ", title)
                if len(parts) >= 2:
                    name = parts[0].strip()
                    role_context = title.lower()
                    
                    # Sanity check: Name shouldn't be the company name or "CEO"
                    if name.lower() in ["ceo", "founder", "owner", "manager"]:
                        continue
                        
                    if "ceo" in role_context or "founder" in role_context or "owner" in role_context:
                        return name, r['link']
        
        return None, None

    def guess_emails(self, name, domain):
        """
        Generates likely email patterns for a name at a domain.
        """
        if not name or not domain:
            return []
            
        # Clean name
        name = re.sub(r"[^\w\s]", "", name) # Remove special chars
        parts = name.lower().split()
        if len(parts) < 1:
            return [f"info@{domain}", f"admin@{domain}"]
            
        f = parts[0]
        l = parts[-1] if len(parts) > 1 else ""
        
        patterns = []
        
        # 1. first@domain.com (High confidence for small biz)
        patterns.append(f"{f}@{domain}")
        
        if l:
            # 2. first.last@domain.com
            patterns.append(f"{f}.{l}@{domain}")
            # 3. first_last@domain.com
            patterns.append(f"{f}_{l}@{domain}")
            # 4. f.last@domain.com
            patterns.append(f"{f[0]}.{l}@{domain}")
            # 5. flast@domain.com
            patterns.append(f"{f}{l}@{domain}")
            
        # Generic fallbacks
        patterns.append(f"info@{domain}")
        patterns.append(f"contact@{domain}")
        patterns.append(f"hello@{domain}")
        
        return list(dict.fromkeys(patterns)) # Deduplicate

    def verify_email_dns(self, email):
        """
        Checks if the domain has MX records.
        Does NOT ping the actual mailbox to avoid blacklisting, 
        but validates that the domain can receive emails.
        """
        try:
            domain = email.split('@')[1]
            dns.resolver.resolve(domain, 'MX')
            return True
        except:
            return False

    def close(self):
        if self.own_driver and self.driver:
            try:
                self.driver.quit()
            except:
                pass
