import os
from dotenv import load_dotenv
from process_emails import main as process_emails_main
from browse_emails import main as browse_emails_main

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    process_emails_main()
    browse_emails_main()
