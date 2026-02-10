import undetected_chromedriver as uc
import sys
import os

print("Diagnostic starting...")
try:
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    
    print("Initializing uc.Chrome...")
    driver = uc.Chrome(options=options, use_subprocess=False)
    print("UC initialized successfully.")
    
    driver.get("https://google.com")
    print(f"Page title: {driver.title}")
    
    driver.quit()
    print("Diagnostic finished successfully.")
except Exception as e:
    print(f"Diagnostic failed: {e}")
    import traceback
    traceback.print_exc()
