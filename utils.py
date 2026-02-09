
import base64
import os
import time
from urllib.parse import urlparse

def canonicalize_website(url):
    try:
        if not url:
            return None
        u = url if url.startswith("http") else f"http://{url}"
        p = urlparse(u)
        host = (p.hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        scheme = p.scheme or "http"
        return f"{scheme}://{host}"
    except:
        return url

def save_base64_image(data, filename, directory="screenshots"):
    """
    Decodes a base64 string and saves it as an image file.
    """
    if not data:
        return None
        
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    filepath = os.path.join(directory, filename)
    
    try:
        # Remove header if present (data:image/jpeg;base64,...)
        if "," in data:
            data = data.split(",")[1]
            
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(data))
        return filepath
    except Exception as e:
        print(f"Error saving screenshot: {e}")
        return None

async def pagespeed(url):
    import httpx
    import config
    import utils
    key = getattr(config, "PAGESPEED_API_KEY", None)
    if not key:
        return None, None
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed", params={"url":url,"key":key,"strategy":"mobile", "category": "performance"})
            if r.status_code != 200:
                return None, None
            data = r.json()
            
            score = None
            screenshot_path = None
            try:
                score = data["lighthouseResult"]["categories"]["performance"]["score"]
            except Exception:
                pass
                
            try:
                # Extract screenshot
                base64_data = data["lighthouseResult"]["audits"]["final-screenshot"]["details"]["data"]
                if base64_data:
                    import re
                    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", url)
                    filename = f"{safe_name}_speed.jpg"
                    screenshot_path = utils.save_base64_image(base64_data, filename, getattr(config, "SCREENSHOT_DIR", "screenshots"))
            except Exception:
                pass
                
            return score, screenshot_path
        except Exception:
            return None, None
