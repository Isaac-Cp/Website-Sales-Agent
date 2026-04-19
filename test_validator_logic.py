import validator
import config

def test_validation():
    test_emails = [
        "p2mise@gmail.com",           # Valid
        "nonexistent_user_12345@gmail.com", # Likely SMTP fail
        "invalid-email",              # Syntax fail
        "sales@brolenhomes.com.au",   # Was failing with 40
        "wght@200..900"               # Scraping junk
    ]
    
    print(f"{'Email':<40} | {'Status':<10} | {'Score':<5} | {'Can Send':<10} | {'Reasons'}")
    print("-" * 100)
    
    for email in test_emails:
        res = validator.validate_email_local(email, allow_risky=True)
        reasons = ", ".join(res.get("reasons", []))
        print(f"{email:<40} | {res['status']:<10} | {res['score']:<5} | {str(res['can_send']):<10} | {reasons}")

if __name__ == "__main__":
    test_validation()
