import json
import os
import datetime
import time
import random
import string
from google_play_scraper import search, app

# Constants
EMAILS_FILE = "FEWDF.json"  # JSON file to store collected emails with timestamps
THRESHOLD = 1000000                        # Maximum allowed realInstalls (≤ 500k)
TARGET_COUNT = 900                        # Total distinct emails to collect per run
SEARCH_RESULTS_PER_QUERY = 100            # Number of search results per query via n_hits

def load_emails():
    """Load stored emails from the JSON file."""
    print("[DEBUG] Loading stored emails...")
    if os.path.exists(EMAILS_FILE):
        try:
            with open(EMAILS_FILE, 'r') as f:
                data = json.load(f)
                print(f"[DEBUG] Loaded {len(data.get('emails', []))} emails from file.")
                return data.get("emails", [])
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode JSON file: {e}")
            return []
    else:
        print("[DEBUG] No existing emails file found.")
        return []

def save_emails(emails):
    """Save the email list with timestamps back to the JSON file."""
    print(f"[DEBUG] Saving {len(emails)} emails to file...")
    with open(EMAILS_FILE, 'w') as f:
        json.dump({"emails": emails}, f, indent=4, default=str)
    print("[DEBUG] Emails saved successfully.")

def cleanup_emails(emails):
    """Remove emails older than 30 days from the list."""
    print("[DEBUG] Cleaning up emails older than 30 days...")
    cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
    updated_emails = []
    for entry in emails:
        try:
            ts = datetime.datetime.fromisoformat(entry["timestamp"])
        except Exception as e:
            print(f"[ERROR] Invalid timestamp format: {e}")
            continue
        if ts >= cutoff:
            updated_emails.append(entry)
    print(f"[DEBUG] Retained {len(updated_emails)} emails after cleanup.")
    return updated_emails

def add_email_to_list(emails, email):
    """Append an email with the current timestamp to the list."""
    emails.append({
        "email": email,
        "timestamp": datetime.datetime.now().isoformat()
    })
    return emails

def load_search_terms():
    """Load search terms from app_names.json."""
    APP_NAMES_FILE = "app_names.json"  # Path to the app names JSON file
    print("[DEBUG] Loading search terms from app_names.json...")
    if os.path.exists(APP_NAMES_FILE):
        try:
            with open(APP_NAMES_FILE, "r") as f:
                data = json.load(f)
                search_terms = data.get("app_names", [])
                if not search_terms:
                    print("[WARNING] No app names found in app_names.json. Using default search terms.")
                    return []
                print(f"[DEBUG] Loaded {len(search_terms)} search terms from app_names.json.")
                return search_terms
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode app_names.json: {e}")
            return []
    else:
        print("[WARNING] app_names.json not found. Using default search terms.")
        return []


def collect_emails(emails):
    """
    Collect TARGET_COUNT distinct developer emails for apps with realInstalls ≤ THRESHOLD,
    while ensuring emails already collected in the past 30 days are not repeated.
    """
    print("[DEBUG] Starting email collection...")
    result_emails = []
    collected_emails_set = {entry["email"].lower() for entry in emails}

    # Load search terms from app_names.json
    search_terms = load_search_terms()
    if not search_terms:
        # Fallback to default search terms if app_names.json is empty or missing
        search_terms = [
            'prototype', 'test', 'early access', 'limited', 'pre-release', 'sandbox',
            'starter', 'minimal', 'concept', 'unreleased', 'beta', 'alpha', 'lite',
            'demo', 'trial', 'preview', 'experimental', 'indie', 'free', 'vpn', 'random'
        ]


    while len(result_emails) < TARGET_COUNT:
        for term in search_terms:
            print(f"[DEBUG] Searching for apps with term '{term}'...")
            try:
                apps = search(term, lang='en', country='us', n_hits=SEARCH_RESULTS_PER_QUERY)
                print(f"[DEBUG] Found {len(apps)} apps for term '{term}'.")
            except Exception as e:
                print(f"[ERROR] Search error for term '{term}': {e}")
                continue

            for app_summary in apps:
                app_id = app_summary.get('appId')

                if not app_id:
                    print("[DEBUG] Skipping app with missing appId.")
                    continue

                print(f"[DEBUG] Fetching details for appId: {app_id}...")
                try:
                    details = app(app_id, lang='en', country='us')
                except Exception as e:
                    print(f"[ERROR] Error fetching details for app {app_id}: {e}")
                    continue

                # Use the numeric field "realInstalls"
                real_installs = details.get('realInstalls')
                if not isinstance(real_installs, int) or real_installs > THRESHOLD:
                    print(f"[DEBUG] Skipped appId {app_id} due to high installs: {real_installs}")
                    continue

                email = details.get('developerEmail')
                if not email:
                    print(f"[DEBUG] No developer email found for appId: {app_id}")
                    continue

                if email.lower() in collected_emails_set:
                    print(f"[DEBUG] Duplicate email skipped: {email}")
                    continue

                # Add the email to the collected set and list
                collected_emails_set.add(email.lower())
                result_emails.append(email)
                emails = add_email_to_list(emails, email)
                print(f"[DEBUG] Collected: {email} (realInstalls: {real_installs})")

                # Save emails in real-time
                save_emails(emails)

                if len(result_emails) >= TARGET_COUNT:
                    break
            if len(result_emails) >= TARGET_COUNT:
                break

        if len(result_emails) < TARGET_COUNT:
            print("[DEBUG] Not enough emails found this cycle. Retrying after a short break...")
            time.sleep(5)

    print(f"[DEBUG] Collected {len(result_emails)} new emails.")
    return result_emails, emails

def main():
    """Main function to orchestrate the email collection process."""
    print("[DEBUG] Starting main process...")
    stored_emails = load_emails()
    stored_emails = cleanup_emails(stored_emails)

    # Collect new emails while respecting the 30-day uniqueness rule
    new_emails, updated_emails = collect_emails(stored_emails)

    # Save the updated email list back to the JSON file
    save_emails(updated_emails)

    # Prepare the JSON output for this run
    result = {
        "collected_emails": new_emails,
        "total_collected": len(new_emails)
    }
    print("[DEBUG] Email collection completed.")
    print(json.dumps(result, indent=4))

if __name__ == "__main__":
    main()


