import os
from email_extractor import extract_emails
from data_storage import save_data, load_data

def main():
    mbox_file = os.getenv('MBOX_FILE_PATH', '../data/summer_camp_newsletters.mbox')
    json_file = os.getenv('JSON_FILE_PATH', '../data/emails_cleaned.json')
    emails = extract_emails(mbox_file)
    save_data(emails, json_file)
    print(f"Processed and saved {len(emails)} emails to {json_file}")

if __name__ == "__main__":
    main()
