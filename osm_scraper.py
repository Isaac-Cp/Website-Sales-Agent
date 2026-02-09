import overpy
import time
try:
    import httpx as _httpx
except Exception:
    _httpx = None

class OsmScraper:
    def __init__(self):
        self.api = overpy.Overpass()
        self.niche_map = {
            "plumber": ['craft="plumber"', 'trade="plumber"'],
            "electrician": ['craft="electrician"', 'trade="electrician"'],
            "hvac": ['craft="hvac"'],
            "roofer": ['craft="roofer"'],
            "carpenter": ['craft="carpenter"'],
            "restaurant": ['amenity="restaurant"'],
            "cafe": ['amenity="cafe"'],
            "dentist": ['amenity="dentist"'],
            "gym": ['leisure="fitness_centre"'],
            "mechanic": ['shop="car_repair"']
        }

    def _get_osm_filter(self, niche):
        niche_lower = niche.lower()
        for key, tags in self.niche_map.items():
            if key in niche_lower:
                return tags
        # Default fallback
        return [f'name~"{niche}"']

    def _geocode_bbox(self, location):
        try:
            headers = {"User-Agent": "SalesAgent/1.0 (contact: none)"}
            params = {"q": location, "format": "json", "limit": 1}
            for attempt in range(3):
                try:
                    with _httpx.Client(timeout=10.0) as client:
                        r = client.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers)
                    if r.status_code == 429:
                        time.sleep(2 * (attempt + 1))
                        continue
                    data = r.json()
                    if not data:
                        return None
                    bbox = data[0].get("boundingbox")
                    south = float(bbox[0]); north = float(bbox[1]); west = float(bbox[2]); east = float(bbox[3])
                    return (south, west, north, east)
                except Exception:
                    time.sleep(1.5 * (attempt + 1))
                    continue
            return None
        except Exception:
            return None

    def scrape(self, query, limit=15):
        """
        Scrapes OpenStreetMap via Overpass API.
        Query: "Plumber near Chicago, IL"
        """
        leads = []
        try:
            niche = query.split(" near ")[0]
            location = query.split(" near ")[-1]
            print(f"[OSM] Searching for '{niche}' in '{location}'...")
            bbox = self._geocode_bbox(location)
            if not bbox:
                print("[OSM] Geocoding failed.")
                return []
            south, west, north, east = bbox
            tags = self._get_osm_filter(niche)
            q_parts = []
            for t in tags:
                q_parts.append(f'node[{t}]({south},{west},{north},{east});')
                q_parts.append(f'way[{t}]({south},{west},{north},{east});')
                q_parts.append(f'relation[{t}]({south},{west},{north},{east});')
            q = "\n".join(q_parts)
            overpass_q = f"""
            [out:json][timeout:25];
            (
              {q}
            );
            out center;
            """
            # Retry Overpass if overloaded
            for attempt in range(3):
                try:
                    result = self.api.query(overpass_q)
                    break
                except Exception as e:
                    msg = str(e).lower()
                    if "too many requests" in msg or "load" in msg or "timed out" in msg:
                        time.sleep(2 * (attempt + 1))
                        continue
                    else:
                        print(f"[OSM] Error: {e}")
                        return []
            else:
                print("[OSM] Overpass overloaded, giving up.")
                return []
            nodes = list(result.nodes) + list(result.ways) + list(result.relations)
            # Convert to leads
            for obj in nodes:
                tags = getattr(obj, "tags", {})
                name = tags.get("name") or "Unknown"
                website = tags.get("website")
                phone = tags.get("phone")
                city = location
                lead = {
                    "business_name": name,
                    "website": website,
                    "phone": phone,
                    "rating": 0.0,
                    "review_count": 0,
                    "description": None,
                    "sample_reviews": None,
                    "source": "osm",
                    "city": city
                }
                leads.append(lead)
                if len(leads) >= limit:
                    break
        except Exception as e:
            print(f"[OSM] Error: {e}")
            return []
        return leads
