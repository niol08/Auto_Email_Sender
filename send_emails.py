import os
import json
import smtplib
import time
import random
from email.message import EmailMessage
from imaplib import IMAP4_SSL

# Constants
SENT_EMAILS_FILE = "sent.json"  # JSON file to track sent emails
EMAIL_LIMIT_PER_ACCOUNT = 450   # Gmail free limit per account
TEST_EMAIL_INTERVAL = 20        # Send a test email after every 20 emails
IMAP_SERVER = "imap.gmail.com"  # IMAP server for Gmail

# Load Gmail accounts from credentials.json
with open("credentials.json", "r") as f:
    ACCOUNTS = json.load(f)

def load_emails_from_json(json_file):
    """Load emails from the specified JSON file."""
    print(f"[DEBUG] Loading emails from {json_file}...")
    if os.path.exists(json_file):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                print(f"[DEBUG] Loaded {len(data.get('emails', []))} emails from {json_file}.")
                return data.get("emails", [])
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode JSON file {json_file}: {e}")
            return []
    else:
        print(f"[ERROR] JSON file {json_file} does not exist.")
        return []

def load_sent_emails():
    """Load already sent emails from the sent.json file."""
    print("[DEBUG] Loading sent emails...")
    if os.path.exists(SENT_EMAILS_FILE):
        try:
            with open(SENT_EMAILS_FILE, "r") as f:
                data = json.load(f)
                print(f"[DEBUG] Loaded {len(data.get('emails', []))} sent emails.")
                return set(data.get("emails", []))
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode sent.json: {e}")
            return set()
    else:
        print("[DEBUG] No sent.json file found. Starting fresh.")
        return set()

def save_sent_email(email):
    """Save a sent email to the sent.json file."""
    print(f"[DEBUG] Saving sent email: {email}")
    sent_emails = load_sent_emails()
    sent_emails.add(email.lower())  # Ensure case-insensitivity
    with open(SENT_EMAILS_FILE, "w") as f:
        json.dump({"emails": list(sent_emails)}, f, indent=4)
    print("[DEBUG] Sent email saved successfully.")

def get_available_account(is_test=False):
    """Get an available Gmail account that hasn't reached its daily limit."""
    for account in ACCOUNTS:
        if is_test and account.get("is_test"):
            return account
        if not is_test and account.get("sent", 0) < EMAIL_LIMIT_PER_ACCOUNT and not account.get("is_test"):
            return account
    return None

def update_credentials():
    """Update the sent count in credentials.json."""
    with open("credentials.json", "w") as f:
        json.dump(ACCOUNTS, f, indent=4)

def send_email(to_email, account):
    """Send an email using the specified Gmail account."""
    msg = EmailMessage()
    msg["Subject"] = "Partnership Opportunity for Google Play Console Owners – Earn Weekly"
    msg["From"] = account["email"]
    msg["To"] = to_email

    # Email Body
    email_body = """\
Dear Developer,

I hope you’re doing well!

My name is Eniola, and I’m reaching out on behalf of NextGen Devs Hub to offer a partnership opportunity for Google Play Console owners like you.

We collaborate with developers to publish apps while ensuring full compliance with Google Play Policies. As a partner, you’ll receive fixed compensation per published app and weekly earnings based on your contributions.

Key Benefits:

✅ $30 per app published  
✅ Weekly payments for every app published  
✅ Earn up to $350 per week (for 10 apps published)  

If you're interested in this opportunity, simply reply with your WhatsApp or Telegram contact, and we’ll provide further details. Alternatively, you can reach out to us directly:

📲 WhatsApp: +234 904 540 9162  
📩 Telegram: @NextGenerationDevs  

Looking forward to collaborating with you!  

Best regards,  
**Eniola Oladejo**  
Partnership Lead | NextGen Devs  

P.S. All app projects strictly comply with Google Play Policies—happy to share more details upfront.  
    """
    msg.set_content(email_body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(account["email"], account["password"])
            smtp.send_message(msg)

        print(f"[DEBUG] Sent to: {to_email} using {account['email']}")
        account["sent"] = account.get("sent", 0) + 1
        save_sent_email(to_email)
        update_credentials()
    except Exception as e:
        print(f"[ERROR] Failed to send from {account['email']} to {to_email}: {e}")

def send_test_email(account):
    """Send a test email to check if emails are being spammed."""
    print("[DEBUG] Sending test email...")
    msg = EmailMessage()
    msg["Subject"] = "Test Email – Spam Check"
    msg["From"] = account["email"]
    msg["To"] = account["email"]  # Send the test email to itself

    # Test Email Body
    email_body = "This is a test email to check if emails are being spammed."
    msg.set_content(email_body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(account["email"], account["password"])
            smtp.send_message(msg)

        print(f"[DEBUG] Test email sent to {account['email']} using {account['email']}")
    except Exception as e:
        print(f"[ERROR] Failed to send test email: {e}")

def check_spam_status(account):
    """Check if the test email is in the Spam folder."""
    print("[DEBUG] Checking spam status for test email...")
    try:
        with IMAP4_SSL(IMAP_SERVER) as imap:
            imap.login(account["email"], account["password"])
            imap.select('"[Gmail]/Spam"')  # Select the Spam folder
            status, messages = imap.search(None, 'ALL')
            if messages[0]:
                print("[ALERT] Test email detected in Spam folder. Terminating process.")
                return True
            print("[DEBUG] Test email not found in Spam folder.")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to check spam status: {e}")
        return False

def main():
    """Main function to send emails."""
    # Ask the user to specify the JSON file to load emails from
    json_file = input("Enter the JSON file to load emails from (e.g., FEWDF.json): ").strip()
    collected_emails = load_emails_from_json(json_file)

    if not collected_emails:
        print("[DEBUG] No emails found in the specified JSON file.")
        return

    # Load already sent emails
    sent_emails = load_sent_emails()

    # Extract email addresses from collected_emails and filter out already sent emails
    unique_emails = [
        email_entry["email"] for email_entry in collected_emails
        if email_entry["email"].lower() not in sent_emails
    ]

    if not unique_emails:
        print("[DEBUG] No new emails to send.")
        return

    print(f"[DEBUG] Found {len(unique_emails)} unique emails to send.")

    # Send emails
    for i, email in enumerate(unique_emails, start=1):
        account = get_available_account()
        if not account:
            print("[DEBUG] All accounts have reached their daily limit.")
            break

        send_email(email, account)

        # Send a test email after every 20 emails
        if i % TEST_EMAIL_INTERVAL == 0:
            test_account = get_available_account(is_test=True)
            if test_account:
                send_test_email(test_account)
                if check_spam_status(test_account):
                    print("[ALERT] Emails are being marked as spam. Please rephrase the email content.")
                    break

        # Add a random delay between emails to reduce sending frequency
        time.sleep(random.uniform(1, 3))  # Random delay between 1 and 3 seconds

    print("[DEBUG] Finished sending emails.")

if __name__ == "__main__":
    main()

