import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

def generate_activities(emails_json):
    prompt = f"""
Given the following JSON file of emails:

{emails_json}

Return a JSON file of activities mentioned in the emails. Use the following fields:

"Activity Title": Extract from email
"Type": Choose from Art, Craft, Science, Cooking, Physical, or Field Trip  
"Description": Write a one sentence description of the activity
"Supplies": List supplies that may be used for the activity
"Instructions": Write a set of instructions for the activity

Output the result as a JSON array, with each activity as a separate object in the array.
"""

    # Call the OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o",
        n=1,
        stop=None,
        temperature=0.7,
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

    # return response.choices[0].text.strip()

# Load emails data
with open('data/emails_cleaned.json', 'r') as file:
    emails_data = json.load(file)

# Convert the emails data to a JSON string
emails_json = json.dumps(emails_data)

# Generate the activities JSON
activities_json = generate_activities(emails_json)

# Save the activities JSON to a file
# with open('data/email_activities.json', 'w') as file:
    # json.dump(activities_json, indent=4)
out_file = open('data/email_activities.json', 'w')
json.dump(activities_json, out_file, indent=4)

print("Activities JSON file generated successfully.")



'''# Process each email
for email in emails:
    body = email['body']
    # Construct the prompt for the OpenAI API
    prompt = f"Extract activity titles, types (art, craft, science, cooking, or physical), and a brief description from the following email content: {body}"
    
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
        extracted_data = extracted_text.split('\n\n')  # Split by double newlines to separate activities

        # Add to activities list
        for activity in extracted_data:
            lines = activity.split('\n')
            if len(lines) > 3:  # Ensure there are enough lines to extract title, type, and description
                print("Debug: ", lines)  # Debug output to check the content of lines
                try:
                    title = lines[1].split(': ')[1].strip()
                    type_ = lines[2].split(': ')[1].strip()
                    description = lines[3].split(': ')[1].strip()
                    activities.append({
                        "title": title,
                        "type": type_,
                        "description": description,
                        "supplies": "",  # To be filled later
                        "instructions": ""  # To be filled later
                    })
                except IndexError as e:
                    print(f"Error processing activity: {activity}, Error: {e}")
    else:
        print("No choices returned from the API.")

# Save the extracted activities to a new JSON file
with open('data/email_activities.json', 'w') as outfile:
    json.dump(activities, outfile, indent=4)

print("Activities extracted and saved successfully.")'''
