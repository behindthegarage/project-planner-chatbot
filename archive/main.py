import os
from dotenv import load_dotenv
import argparse
import sys
sys.path.append('/home/user/project-planner-chatbot/src')

from process_emails import main as process_emails_main
from browse_emails import main as browse_emails_main
from data_extraction import extract_from_json, extract_from_csv, extract_from_txt
from data_cleaning import clean_text, preprocess_text, clean_tabular_data
from data_storage import save_data

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Run email processing and data handling tasks.")
    parser.add_argument('--process-emails', action='store_true', help='Process emails from mbox file')
    args = parser.parse_args()

    if args.process_emails:
        # Process emails only if --process-emails is specified
        process_emails_main()

    # Always run these parts
    browse_emails_main()

    # Example of data extraction, cleaning, and storage
    json_data = extract_from_json(os.getenv('JSON_FILE_PATH'))
    csv_data = extract_from_csv(os.getenv('CSV_FILE_PATH'))
    txt_data = extract_from_txt(os.getenv('TXT_FILE_PATH'))

    cleaned_txt = clean_text(txt_data)
    preprocessed_txt = preprocess_text(cleaned_txt)
    cleaned_csv_data = clean_tabular_data(csv_data)

    save_data(cleaned_csv_data, os.getenv('CLEANED_CSV_OUTPUT'))
    save_data({'preprocessed_text': preprocessed_txt}, os.getenv('PREPROCESSED_TXT_OUTPUT'))

if __name__ == "__main__":
    main()
