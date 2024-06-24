import streamlit as st
import sqlite3
import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Get API keys and index name from environment variables
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')

if not pinecone_api_key or not pinecone_index_name:
    raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_NAME must be set in the environment variables.")

# Initialize Pinecone
pc = Pinecone(api_key=pinecone_api_key)

# Connect to the Pinecone index
index = pc.Index(pinecone_index_name)

def get_embedding(text):
    response = client.embeddings.create(input=text, model="text-embedding-3-large")
    return response.data[0].embedding

def parse_activities(text):
    activities = []
    current_activity = {}
    current_field = None

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            if current_activity:
                activities.append(current_activity)
                current_activity = {}
            current_field = None
        elif ':' in line:
            key, value = line.split(':', 1)
            key = key.lower()
            if key in ['type', 'description', 'supplies', 'instructions']:
                current_activity[key] = value.strip()
                current_field = key
            elif 'title' not in current_activity:
                # If we haven't set a title yet, this line becomes the title
                current_activity['title'] = line.strip()
        elif 'title' not in current_activity:
            # If this is the first line and doesn't contain a colon, it's the title
            current_activity['title'] = line
        elif current_field:
            current_activity[current_field] += ' ' + line

    if current_activity:
        activities.append(current_activity)

    return activities

def add_activity(conn, cursor, index, activity):
    required_fields = ['title', 'type', 'description', 'supplies', 'instructions']
    
    # Check if all required fields are present
    missing_fields = [field for field in required_fields if field not in activity]
    if missing_fields:
        raise ValueError(f"Activity is missing required fields: {', '.join(missing_fields)}")

    # Insert the new activity into the database
    insert_query = """
    INSERT INTO activities (title, type, description, supplies, instructions)
    VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(insert_query, (
        activity['title'],
        activity.get('type', ''),
        activity.get('description', ''),
        activity.get('supplies', ''),
        activity.get('instructions', '')
    ))
    conn.commit()
    
    # Fetch the last inserted activity ID
    activity_id = cursor.lastrowid
    
    # Create a combined text from title, description, supplies, and instructions
    text = (
        f"Title: {activity['title']}\n"
        f"Description: {activity.get('description', '')}\n"
        f"Supplies: {activity.get('supplies', '')}\n"
        f"Instructions: {activity.get('instructions', '')}"
    )
    
    # Generate embedding for the combined text
    embedding = get_embedding(text)
    
    # Upsert the embedding into Pinecone with the type as metadata
    index.upsert(vectors=[{
        "id": str(activity_id),
        "values": embedding,
        "metadata": {"type": activity.get('type', '')}
    }])

# Streamlit app
st.title('Bulk Add Activities')

# User input for multiple activities
activities_input = st.text_area('Enter multiple activities (separate each activity with a blank line)', height=300)

if st.button('Add Activities'):
    if activities_input:
        # Parse the input into individual activities
        activities = parse_activities(activities_input)
        
        # Connect to the SQLite database
        conn = sqlite3.connect('activities.db')
        cursor = conn.cursor()
        
        # Add each activity to the database and Pinecone index
        success_count = 0
        for activity in activities:
            try:
                add_activity(conn, cursor, index, activity)
                success_count += 1
            except ValueError as e:
                st.error(f"Error adding activity: {str(e)}")
            except Exception as e:
                st.error(f"Unexpected error adding activity: {str(e)}")
        
        # Close the database connection
        conn.close()
        
        if success_count > 0:
            st.success(f'{success_count} activities added and embedded successfully!')
        if success_count < len(activities):
            st.warning(f'{len(activities) - success_count} activities failed to add. Please check the errors above.')
    else:
        st.error('Please enter at least one activity.')