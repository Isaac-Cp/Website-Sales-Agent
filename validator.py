import requests
import config

def validate_email_api(email):
    """
    Validates email using the configured 3rd party provider.
    Returns:
        True: Valid / Deliverable
        False: Invalid / Undeliverable
        None: Unknown / Error (Fallback to SMTP probe recommended)
    """
    provider = config.VALIDATION_PROVIDER.lower()
    
    if provider == "hunter":
        return _validate_hunter(email)
    elif provider == "zerobounce":
        return _validate_zerobounce(email)
    
    # Default to None so the caller knows to use fallback
    return None

def _validate_hunter(email):
    if not config.HUNTER_API_KEY:
        print("[Validator] Hunter API Key missing.")
        return None
        
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={config.HUNTER_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "data" in data:
            status = data["data"]["status"]
            # Hunter statuses: valid, invalid, accept_all (risky), webmail, disposable, unknown
            # We want 'valid'. 'accept_all' is risky (catch-all).
            if status == "valid":
                return True
            elif status == "invalid":
                return False
            else:
                print(f"[Validator] Hunter status: {status} for {email}")
                # For high quality, we might only want 'valid'.
                # But 'accept_all' is common for businesses.
                # User requested "Advanced Validation" to avoid "Address not found".
                # Safest is to return False for accept_all if we want 100% inbox, 
                # but that might kill too many leads. 
                # Let's return False for 'invalid' and None for others (let SMTP probe decide or skip).
                return None 
    except Exception as e:
        print(f"[Validator] Hunter API error: {e}")
        return None

def _validate_zerobounce(email):
    # Placeholder for ZeroBounce implementation
    # Requires API key and endpoint
    return None
