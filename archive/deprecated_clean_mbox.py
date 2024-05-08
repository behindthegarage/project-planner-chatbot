import mailbox
import json
import re
import os

def clean_email_addresses(text):
    # Regex to find email addresses
    return re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)

def extract_emails(mbox_file):
    mbox = mailbox.mbox(mbox_file)
    emails = []

    for message in mbox:
        subject = message['subject'] if message['subject'] else ""
        print(f"Processing subject: {subject}")  # Debugging line
        if 're:' in subject.lower() or "delivery status notification (failure)" in subject.lower():
            print(f"Skipping email: {subject}")  # Additional debugging line
            continue
        body = ""

        if message.is_multipart():
            for part in message.walk():
                # Check if the content type of the part is text/plain
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break  # Once the plain text part is found, stop looking
        else:
            payload = message.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')

        # Clean email addresses from subject and body
        clean_subject = clean_email_addresses(subject)
        clean_body = clean_email_addresses(body)
        emails.append({'subject': clean_subject, 'body': clean_body})

    return emails

def save_to_json(emails, output_file):
    with open(output_file, 'w') as f:
        json.dump(emails, f, indent=4)

def load_emails_from_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def browse_emails(emails):
    index = 0
    total_emails = len(emails)
    print(f"Total emails: {total_emails}")

    while True:
        print(f"Email {index + 1}/{total_emails}")
        print(f"Subject: {emails[index]['subject']}")
        print(f"Body: {emails[index]['body']}\n")

        command = input("Enter 'n' for next, 'p' for previous, or 'q' to quit: ").strip().lower()
        if command == 'n':
            if index < total_emails - 1:
                index += 1
            else:
                print("This is the last email.")
        elif command == 'p':
            if index > 0:
                index -= 1
            else:
                print("This is the first email.")
        elif command == 'q':
            break
        else:
            print("Invalid command. Please try again.")

def main():
    mbox_file = 'summer_camp_newsletters.mbox'
    output_file = 'emails_cleaned.json'

    # Clear the output file at the start
    if os.path.exists(output_file):
        os.remove(output_file)

    emails = extract_emails(mbox_file)
    save_to_json(emails, output_file)

    # Load emails from JSON and browse
    emails = load_emails_from_json(output_file)
    browse_emails(emails)

if __name__ == "__main__":
    main()

