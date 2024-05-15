import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

# Load emails data
with open('data/emails_cleaned.json', 'r') as file:
    emails = json.load(file)

# Prepare the output list
titles = []

# Process each email
for email in emails:
    body = email['body']
    # Construct the prompt for the OpenAI API
    prompt = f"Extract activity titles from the following email content: {body}"
    
    # Call the OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    # Access the response data correctly
    if response.choices:
        extracted_text = response.choices[0].message.content.strip()
        extracted_data = extracted_text.split('\n')  # Split by newlines to separate titles

        # Add to titles list
        for title in extracted_data:
            if title:  # Ensure the title is not empty
                titles.append(title.strip())
    else:
        print("No choices returned from the API.")

# Save the extracted titles to a new JSON file
with open('data/email_titles_simple.json', 'w') as outfile:
    json.dump(titles, outfile, indent=4)

print("Titles extracted and saved successfully.")

