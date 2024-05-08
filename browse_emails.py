import json

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
    file_path = 'emails_cleaned.json'
    emails = load_emails_from_json(file_path)
    browse_emails(emails)

if __name__ == "__main__":
    main()