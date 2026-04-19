import config
from mailer import Mailer

def test_all():
    smtp_accounts = config.get_smtp_accounts()
    print(f"Testing {len(smtp_accounts)} accounts...")
    for a in smtp_accounts:
        mailer = Mailer(a["email"], a["password"], a["server"], a["port"])
        print(f"Testing {a['email']}...")
        if mailer.test_connection():
            print(f"  [OK] {a['email']} is working.")
        else:
            print(f"  [FAIL] {a['email']} failed.")

if __name__ == "__main__":
    test_all()
