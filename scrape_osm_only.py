from osm_scraper import OsmScraper
from database import DataManager
import config

def scrape_more():
    osm = OsmScraper()
    dm = DataManager()
    
    queries = [
        "Roofing near New York, NY, USA",
        "Electrician near Sydney, Australia",
        "Plumber near Melbourne, Australia"
    ]
    
    for query in queries:
        print(f"Scraping OSM for: {query}")
        leads = osm.scrape(query, limit=20)
        print(f"  Found {len(leads)} leads.")
        for lead in leads:
            dm.save_lead(lead)
    
    print("Scraping complete.")

if __name__ == "__main__":
    scrape_more()
