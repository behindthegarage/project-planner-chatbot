import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

def generate_activities(text_content, filename):
    prompt = f"""
    Given the following text content:

    {text_content}

    Identify any art, craft, science, cooking, or physical activities that could be done by children in a summer camp, childcare facility, at home, or on their own.

    For each activity, provide the following details:
    "Activity Title": Extract from text
    "Type": Choose from Art, Craft, Science, Cooking, Physical
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

    # Save the API response to a JSON file
    json_output_dir = 'data/json/'
    os.makedirs(json_output_dir, exist_ok=True)
    json_output_path = os.path.join(json_output_dir, f'{filename}.json')
    with open(json_output_path, 'w') as json_file:
        json.dump(api_response_content, json_file, indent=4)

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
    not_applicable_files = []

    input_dir = 'data/google/'
    output_file = 'data/google_activities.json'
    not_applicable_file = 'data/not_applicable.txt'

    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        if os.path.isfile(file_path):
            print(f"Analyzing file: {filename}")
            with open(file_path, 'r') as file:
                text_content = file.read()

            activities_json = generate_activities(text_content, filename)
            if activities_json:
                all_activities.extend(activities_json)
            else:
                not_applicable_files.append(filename)

    if all_activities:
        with open(output_file, 'w') as file:
            json.dump(all_activities, file, indent=4)
        print("Activities JSON file generated successfully with all activities.")
    else:
        print("No activities to save.")

    if not_applicable_files:
        with open(not_applicable_file, 'w') as file:
            for filename in not_applicable_files:
                file.write(f"{filename}\n")
        print("Not applicable files list generated successfully.")

# Run the processing function
process_files()