from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import os

# Constants
URL = "https://www.appbrain.com/apps/trending/free"
OUTPUT_FILE = "app_names.json"  # File to save the scraped app names
SCROLL_PAUSE_TIME = 2  # Pause time between scrolls
MAX_SCROLLS = 50  # Maximum number of scrolls to perform

def load_existing_app_names():
    """Load previously scraped app names from the JSON file."""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r") as f:
                data = json.load(f)
                print(f"[DEBUG] Loaded {len(data.get('app_names', []))} existing app names from {OUTPUT_FILE}.")
                return set(data.get("app_names", []))
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode {OUTPUT_FILE}: {e}")
            return set()
    else:
        print("[DEBUG] No existing app names file found. Starting fresh.")
        return set()

def save_app_names(app_names):
    """Save the scraped app names to a JSON file."""
    print(f"[DEBUG] Saving {len(app_names)} app names to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump({"app_names": list(app_names)}, f, indent=4)
    print("[DEBUG] App names saved successfully.")

def scrape_app_names():
    """Scrape app names from the AppBrain website."""
    print("[DEBUG] Starting the scraping process...")

    # Load existing app names
    app_names = load_existing_app_names()

    # Set up Selenium WebDriver (use ChromeDriver or another driver of your choice)
    driver = webdriver.Chrome()  # Ensure you have the ChromeDriver installed and in PATH
    driver.get(URL)

    try:
        # Perform infinite scrolling
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0

        while scroll_count < MAX_SCROLLS:
            print(f"[DEBUG] Scrolling... ({scroll_count + 1}/{MAX_SCROLLS})")

            # Scroll to the bottom of the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)  # Wait for the page to load

            # Extract app names from the current view
            app_elements = driver.find_elements(By.CSS_SELECTOR, "div.browse-app-large-title")
            for element in app_elements:
                app_name = element.text.strip()
                if app_name and app_name not in app_names:
                    app_names.add(app_name)
                    print(f"[DEBUG] Added app name: {app_name}")

            # Save progress incrementally
            save_app_names(app_names)

            # Check if we've reached the bottom of the page
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("[DEBUG] Reached the bottom of the page.")
                break
            last_height = new_height
            scroll_count += 1

    except Exception as e:
        print(f"[ERROR] An error occurred during scraping: {e}")
    finally:
        # Close the browser
        driver.quit()

    print(f"[DEBUG] Scraping completed. {len(app_names)} app names saved to {OUTPUT_FILE}.")

if __name__ == "__main__":
    scrape_app_names()