import os
import json
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

def generate_activities(theme):
    prompt = f"""
    Given the theme "{theme}", create 3 art, 3 craft, 3 science, 3 cooking, and 3 physical activities for children. For each activity, provide the following details:
    "Activity Title": Create a title for the activity
    "Type": Specify "Art" or "Craft" or "Science" or "Cooking" or "Physical"
    "Description": Write a one sentence description of the activity
    "Supplies": List supplies that may be used for the activity
    "Instructions": Write a set of instructions for the activity

    Output the result as a JSON array, with each activity as a separate object in the array.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        n=1,
        stop=None,
        temperature=1.2,
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

    try:
        # Extract the valid JSON part from the response content
        json_start = api_response_content.find("[")
        json_end = api_response_content.rfind("]") + 1
        json_content = api_response_content[json_start:json_end]

        return json.loads(json_content)
    except (json.JSONDecodeError, ValueError) as e:
        st.error("Failed to decode JSON from API response.")
        st.error(f"Error: {e}")
        return None

# Streamlit interface
st.title("Activity Generator")
theme = st.text_input("Enter a theme for the activities:")

if st.button("Generate Activities"):
    if theme:
        activities = generate_activities(theme)
        if activities:
            st.success("Activities generated successfully!")
            for activity in activities:
                st.subheader(activity["Activity Title"])
                st.write(f"**Type**: {activity['Type']}")
                st.write(f"**Description**: {activity['Description']}")
                st.write("**Supplies**:")
                st.write("\n".join(activity['Supplies']))
                st.write("**Instructions**:")
                st.write("\n".join(activity['Instructions']))
        else:
            st.error("No activities generated.")
    else:
        st.error("Please enter a theme.")