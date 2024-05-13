import mailbox
import re

def clean_email_addresses(text):
    """Remove email addresses from text using regex."""
    return re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)

def extract_emails(mbox_file):
    """Extract emails from an mbox file, cleaning each email."""
    mbox = mailbox.mbox(mbox_file)
    emails = []
    for message in mbox:
        if should_skip_email(message['subject']):
            continue
        subject, body = get_email_content(message)
        emails.append({'subject': clean_email_addresses(subject), 'body': clean_email_addresses(body)})
    return emails

def should_skip_email(subject):
    """Determine if an email should be skipped based on its subject."""
    subject = subject.lower() if subject else ""
    return 're:' in subject or "delivery status notification (failure)" in subject

def get_email_content(message):
    """Retrieve and return the subject and body of an email."""
    subject = message['subject'] if message['subject'] else ""
    body = extract_body(message)
    return subject, body

def extract_body(message):
    """Extract the body of the email, preferring text/plain content."""
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == 'text/plain':
                return part.get_payload(decode=True).decode('utf-8', errors='ignore')
    else:
        payload = message.get_payload(decode=True)
        return payload.decode('utf-8', errors='ignore') if payload else ""