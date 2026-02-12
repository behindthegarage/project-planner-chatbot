import os
import json
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv
import sqlite3
from openai import OpenAI
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize Pinecone
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')

if not pinecone_api_key or not pinecone_index_name:
    raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_NAME must be set in the environment variables.")

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index(pinecone_index_name)

# Initialize session state
if 'activities' not in st.session_state:
    st.session_state.activities = []

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
        # Extract the valid JSON part from the response content
        json_start = api_response_content.find("[")
        json_end = api_response_content.rfind("]") + 1
        json_content = api_response_content[json_start:json_end]

        return json.loads(json_content)
    except (json.JSONDecodeError, ValueError) as e:
        st.error("Failed to decode JSON from API response.")
        st.error(f"Error: {e}")
        return None

def get_embedding(text):
    response = openai_client.embeddings.create(input=text, model="text-embedding-3-large")
    return response.data[0].embedding

def add_activity(conn, cursor, index, activity):
    insert_query = """
    INSERT INTO activities (title, type, description, supplies, instructions, to_do, source)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(insert_query, (
        activity['Activity Title'],
        activity['Type'],
        activity['Description'],
        ', '.join(activity['Supplies']),
        '\n'.join(activity['Instructions']),
        True,  # Set to_do to True by default
        "AI"   # Set source to "AI"
    ))
    conn.commit()
    
    activity_id = cursor.lastrowid
    
    text = (
        f"Title: {activity['Activity Title']}\n"
        f"Description: {activity['Description']}\n"
        f"Supplies: {', '.join(activity['Supplies'])}\n"
        f"Instructions: {' '.join(activity['Instructions'])}"
    )
    
    embedding = get_embedding(text)
    
    index.upsert(vectors=[{
        "id": str(activity_id),
        "values": embedding,
        "metadata": {
            "type": activity['Type'],
            "to_do": True
        }
    }])

# Streamlit interface
st.title("Activity Generator")
theme = st.text_input("Enter a theme for the activities:")

if st.button("Generate Activities"):
    if theme:
        st.session_state.activities = generate_activities(theme)
        if st.session_state.activities:
            st.success("Activities generated successfully!")
        else:
            st.error("No activities generated.")
    else:
        st.error("Please enter a theme.")

# Display activities and selection checkboxes
if st.session_state.activities:
    for i, activity in enumerate(st.session_state.activities):
        st.subheader(activity["Activity Title"])
        st.write(f"**Type**: {activity['Type']}")
        st.write(f"**Description**: {activity['Description']}")
        st.write("**Supplies**:")
        st.write(", ".join(activity['Supplies']))
        st.write("**Instructions**:")
        st.write("\n".join(activity['Instructions']))
        
        # Use a unique key for each checkbox
        key = f"checkbox_{i}_{activity['Activity Title']}"
        activity['selected'] = st.checkbox("Select this activity", key=key, value=activity.get('selected', False))

if st.button("Add Selected Activities"):
    selected_activities = [activity for activity in st.session_state.activities if activity.get('selected', False)]
    if selected_activities:
        conn = sqlite3.connect('activities.db')
        cursor = conn.cursor()
        
        success_count = 0
        for activity in selected_activities:
            try:
                add_activity(conn, cursor, index, activity)
                success_count += 1
            except Exception as e:
                st.error(f"Error adding activity '{activity['Activity Title']}': {str(e)}")
        
        conn.close()
        
        if success_count > 0:
            st.success(f'{success_count} activities added and embedded successfully!')
        if success_count < len(selected_activities):
            st.warning(f'{len(selected_activities) - success_count} activities failed to add. Please check the errors above.')
    else:
        st.warning("No activities selected. Please select at least one activity to add.")