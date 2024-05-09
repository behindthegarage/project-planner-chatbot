from openai import OpenAI
import json
import os
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

def load_emails():
    with open('emails_cleaned.json', 'r') as file:
        return json.load(file)

def chat_with_openai(prompt, context):
    response = client.chat.completions.create(model="gpt-4-turbo-2024-04-09",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": context},
        {"role": "user", "content": prompt}
    ],
    )
    return response.choices[0].message.content

def main():
    emails = load_emails()
    # Limit the number of emails used for context
    limited_emails = emails[:10]  # Adjust the number based on average email length
    context = " ".join([email['body'] for email in limited_emails])  # Simplified context
    print("Welcome to the Project Planner Chatbot. Type 'quit' to exit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("Exiting chat...")
            break
        response = chat_with_openai(user_input, context)
        print("Chatbot:", response)

if __name__ == "__main__":
    main()

