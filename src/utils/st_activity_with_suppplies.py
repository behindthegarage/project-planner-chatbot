import os
import json
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def generate_activities_with_supplies_and_theme(supplies, theme):
    prompt = f"""
    Given the following list of supplies: {', '.join(supplies)}, and the theme "{theme}", create 3 art, 3 craft, 3 science, 3 cooking, and 3 physical activities for children that use some or all of these supplies and relate to the theme. For each activity, provide the following details:
    "Activity Title": Create a title for the activity
    "Type": Specify "Art" or "Craft" or "Science" or "Cooking" or "Physical"
    "Description": Write a one sentence description of the activity
    "Supplies": List supplies from the given list that are used for the activity
    "Instructions": Write a set of instructions for the activity

    Output the result as a JSON array, with each activity as a separate object in the array.
    """

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4000,
        temperature=0.7,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    api_response_content = response.content[0].text

    try:
        json_start = api_response_content.find("[")
        json_end = api_response_content.rfind("]") + 1
        json_content = api_response_content[json_start:json_end]

        return json.loads(json_content)
    except (json.JSONDecodeError, ValueError) as e:
        st.error("Failed to decode JSON from API response.")
        st.error(f"Error: {e}")
        return None

# Streamlit interface
st.title("Activity Generator with Supplies and Theme")

# Input for theme
theme = st.text_input("Enter a theme for the activities:")

# Input for supplies
supplies_input = st.text_area("Enter supplies (one per line):")
supplies_list = [supply.strip() for supply in supplies_input.split('\n') if supply.strip()]

if st.button("Generate Activities"):
    if supplies_list and theme:
        activities = generate_activities_with_supplies_and_theme(supplies_list, theme)
        if activities:
            st.success("Activities generated successfully!")
            for activity in activities:
                st.subheader(activity["Activity Title"])
                st.write(f"**Type**: {activity['Type']}")
                st.write(f"**Description**: {activity['Description']}")
                st.write("**Supplies**:")
                st.write(", ".join(activity['Supplies']))
                st.write("**Instructions**:")
                st.write("\n".join(activity['Instructions']))
        else:
            st.error("No activities generated.")
    else:
        st.error("Please enter at least one supply and a theme.")