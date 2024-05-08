from email_extractor import extract_emails
from data_storage import save_to_json, load_from_json

def main():
    mbox_file = 'summer_camp_newsletters.mbox'  # Adjust the file name as necessary
    json_file = 'emails_cleaned.json'
    emails = extract_emails(mbox_file)
    save_to_json(emails, json_file)
    print(f"Processed and saved {len(emails)} emails to {json_file}")

if __name__ == "__main__":
    main()
