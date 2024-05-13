from vector_store_utils import setup_vector_store  # Updated import path and possibly name

def main():
    # Specify the path to your cleaned emails JSON file
    
    filepath = '../data/emails_cleaned.json'  # Updated path if data is in a separate directory
    setup_vector_store(filepath)
    print("Vector store setup is complete.")

if __name__ == "__main__":
    main()
