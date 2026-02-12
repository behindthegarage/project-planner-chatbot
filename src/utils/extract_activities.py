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

    api_response_content = response.choices[0].message.content
    print("API Response Content:", api_response_content)

    if api_response_content:
        try:
            # Extract the valid JSON part from the response content
            json_start = api_response_content.find("[")
            json_end = api_response_content.rfind("]") + 1
            json_content = api_response_content[json_start:json_end]

            return json.loads(json_content)
        except (json.JSONDecodeError, ValueError) as e:
            print("Failed to decode JSON from API response:", e)
            print("API Response Content:", api_response_content)  # Log the actual response content
            return None
    else:
        print("API response is empty.")
        return None

def process_files():
    all_activities = []
    for i in range(1, 6):  # Assuming there are 5 files
        file_path = f'data/emails_chunk_{i}.json'
        with open(file_path, 'r') as file:
            emails_data = json.load(file)
        emails_json = json.dumps(emails_data)
        activities_json = generate_activities(emails_json)
        if activities_json:
            all_activities.extend(activities_json)

    if all_activities:
        with open('data/email_activities.json', 'w') as file:
            json.dump(all_activities, file, indent=4)
        print("Activities JSON file generated successfully with all activities.")
    else:
        print("No activities to save.")

# Run the processing function
process_files()

