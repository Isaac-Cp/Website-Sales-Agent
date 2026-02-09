import concurrent.futures
import config
import utils

def run_parallel_scraping(query, google_scraper, driver, yelp_api, osm):
    """
    Runs multiple scrapers in parallel and merges results.
    """
    print(f"\n[Parallel Scraping] Starting threads for: {query}")
    results = []
    
    # Define wrapper functions for thread safety
    def run_google():
        try:
            return google_scraper.scrape_google_maps(driver, query)
        except Exception as e:
            print(f"[GoogleMaps] Error: {e}")
            return []

    def run_yelp_api():
        try:
            return yelp_api.scrape(query)
        except Exception as e:
            print(f"[YelpAPI] Error: {e}")
            return []

    def run_osm():
        try:
            return osm.scrape(query)
        except Exception as e:
            print(f"[OSM] Error: {e}")
            return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=getattr(config, "PARALLEL_WORKERS", 4)) as executor:
        future_google = executor.submit(run_google)
        future_yelp_api = executor.submit(run_yelp_api)
        future_osm = executor.submit(run_osm)
        
        # Collect results as they finish
        futures = {
            future_google: "GoogleMaps",
            future_yelp_api: "YelpAPI",
            future_osm: "OSM"
        }
        for future in concurrent.futures.as_completed(futures):
            source_name = futures[future]
            try:
                data = future.result()
                count = len(data) if data else 0
                print(f"[Parallel] {source_name} returned {count} leads.")
                if data:
                    results.extend(data)
            except Exception as e:
                print(f"[Parallel] {source_name} Thread Error: {e}")
                
    # Deduplicate
    unique_leads = {}
    for lead in results:
        # Key by website (if exists) or Name+City
        key = None
        if lead.get('website'):
            key = utils.canonicalize_website(lead['website'])
        else:
            key = f"{lead['business_name']}|{lead.get('city', '')}"
        
        if key not in unique_leads:
            unique_leads[key] = lead
        else:
            # Merge data? (Optional improvement: keep the one with more info)
            pass
            
    print(f"[Parallel Scraping] Total unique leads found: {len(unique_leads)}")
    return list(unique_leads.values())
