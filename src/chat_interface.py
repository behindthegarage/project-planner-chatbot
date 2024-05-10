import json
import os
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

def load_emails():
    with open('../data/emails_cleaned.json', 'r') as file:
        return json.load(file)

def main():
    emails = load_emails()
    print("Welcome to the Project Planner Chatbot. Type 'quit' to exit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("Exiting chat...")
            break
        # Simulate a response for demonstration
        print("Chatbot:", "Thank you for your message.")

if __name__ == "__main__":
    main()
    