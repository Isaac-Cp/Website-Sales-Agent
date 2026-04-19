if __name__ == "__main__":
    import time
    print("Importing config...")
    import config
    print("Importing database...")
    from database import DataManager
    print("Initializing DataManager...")
    dm = DataManager()
    print("DB initialized.")
    print("Importing Scraper...")
    from scraper import Scraper
    print("Initializing Scraper...")
    scraper = Scraper(headless=True)
    print("Scraper initialized.")
    print("Starting driver...")
    driver = scraper.get_driver()
    print("Driver started.")
    scraper.cleanup()
    print("Done.")
