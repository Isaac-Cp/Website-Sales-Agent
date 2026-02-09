import imap_tracker
import time
import sys

def monitor_bounces():
    print("Checking inbox for new bounce reports...")
    print("Press Ctrl+C to stop monitoring.\n")
    
    total_bounces = 0
    
    try:
        while True:
            events = imap_tracker.fetch_outcomes()
            new_bounces = [e for e in events if e.get("type") == "bounce"]
            
            if new_bounces:
                print(f"[{time.strftime('%H:%M:%S')}] Found {len(new_bounces)} NEW bounce notification(s).")
                for b in new_bounces:
                    print(f"  -> Bounce for: {b.get('email')} (Subject: {b.get('meta', {}).get('subject')})")
                total_bounces += len(new_bounces)
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                
            time.sleep(60) # Check every minute
            
    except KeyboardInterrupt:
        print(f"\n\nStopped. Total new bounces detected in this session: {total_bounces}")

if __name__ == "__main__":
    monitor_bounces()
