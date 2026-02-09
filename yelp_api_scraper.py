import config
from yelpapi import YelpAPI
import json

class YelpApiScraper:
    def __init__(self, api_key=None):
        self.api_key = api_key or config.YELP_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = YelpAPI(self.api_key, timeout_s=5.0)
            except Exception as e:
                print(f"[YelpAPI] Failed to initialize: {e}")

    def scrape(self, query, limit=15):
        """
        Scrapes Yelp Fusion API for businesses matching the query.
        Query format expected: "Plumber near Chicago, IL"
        """
        if not self.client:
            print("[YelpAPI] Skipped: No API Key provided.")
            return []

        leads = []
        try:
            # Parse location from query
            term = query.split(" near ")[0] if " near " in query else query
            location = query.split(" near ")[-1] if " near " in query else "USA"

            # Search API
            print(f"[YelpAPI] Searching for '{term}' in '{location}'...")
            response = self.client.search_query(
                term=term,
                location=location,
                limit=limit,
                sort_by='best_match'
            )

            businesses = response.get('businesses', [])
            for b in businesses:
                # Convert Yelp data to our standardized lead format
                website = b.get('url', '').split('?')[0] # Clean tracking params
                
                # Note: Yelp API doesn't always give the direct business website, 
                # mostly the Yelp page. We might need to visit the Yelp page to get the real URL
                # but for speed, we'll store what we have.
                # However, for the automation to work best, we need the REAL website.
                # The 'url' field in API response is the Yelp Page URL.
                # We can flag this source so the main scraper knows to 'deep scrape' the Yelp page if needed.
                
                lead = {
                    "business_name": b.get('name'),
                    "website": None, # Yelp API v3 Business Search often doesn't return the direct business website
                    "yelp_url": website,
                    "phone": b.get('phone') or b.get('display_phone'),
                    "rating": b.get('rating'),
                    "review_count": b.get('review_count'),
                    "description": ", ".join([c['title'] for c in b.get('categories', [])]),
                    "sample_reviews": None, # Requires separate API call (/businesses/{id}/reviews)
                    "source": "yelp_api",
                    "city": b.get('location', {}).get('city'),
                    "address": ", ".join(b.get('location', {}).get('display_address', []))
                }
                leads.append(lead)

        except Exception as e:
            print(f"[YelpAPI] Error: {e}")
        
        return leads

    def cleanup(self):
        # yelpapi uses requests.Session under the hood but doesn't expose a close method easily 
        # unless used as context manager. Since we instantiated it directly, we let GC handle it.
        pass
