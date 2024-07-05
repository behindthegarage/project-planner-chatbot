import streamlit as st
import sqlite3
import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI and Pinecone clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
pinecone_client = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
pinecone_index = pinecone_client.Index(os.getenv('PINECONE_INDEX_NAME'))

def get_embedding(text):
    """Generate embedding for the given text using OpenAI."""
    response = openai_client.embeddings.create(input=text, model="text-embedding-3-large")
    return response.data[0].embedding

def fetch_activities_by_ids(activity_ids):
    """Fetch activities from SQLite database by IDs."""
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    placeholders = ', '.join('?' for _ in activity_ids)
    query = f"SELECT * FROM activities WHERE id IN ({placeholders})"
    cursor.execute(query, activity_ids)
    activities = cursor.fetchall()
    conn.close()
    return activities

def search_activities(keyword, top_k=4):
    """Search for activities based on keyword and return top 2 matches for each type."""
    embedding = get_embedding(keyword)
    activity_types = ['Art', 'Craft', 'Science', 'Cooking']
    results = {}
    for activity_type in activity_types:
        query_results = pinecone_index.query(vector=embedding, top_k=top_k, filter={"type": activity_type}, include_metadata=True)
        results[activity_type] = [result['id'] for result in query_results['matches']]
    return results

def update_activity(id, title, type, description, supplies, instructions, source, to_do):
    """Update an activity in the database."""
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE activities
    SET title = ?, type = ?, description = ?, supplies = ?, instructions = ?, source = ?, to_do = ?
    WHERE id = ?
    ''', (title, type, description, supplies, instructions, source, to_do, id))
    conn.commit()
    conn.close()

def update_multiple_activities(activities_to_update):
    """Update multiple activities' to_do status in the database."""
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    for activity_id, to_do in activities_to_update.items():
        cursor.execute('''
        UPDATE activities
        SET to_do = ?
        WHERE id = ?
        ''', (to_do, activity_id))
    conn.commit()
    conn.close()

# Initialize session state for search results and todo states
if 'search_results' not in st.session_state:
    st.session_state.search_results = {}
if 'todo_states' not in st.session_state:
    st.session_state.todo_states = {}

# Streamlit UI
st.title('Activity Search')

# Use a form for the search to prevent automatic reruns
with st.form(key='search_form'):
    theme_description = st.text_input('Enter a theme description:')
    search_button = st.form_submit_button('Search')

if search_button and theme_description:
    st.session_state.search_results = search_activities(theme_description)

# Display search results and checkboxes
if st.session_state.search_results:
    for activity_type, ids in st.session_state.search_results.items():
        if ids:
            activities = fetch_activities_by_ids(ids)
            if activities:
                st.subheader(f"{activity_type} Activities:")
                for activity in activities:
                    st.write(f"ID: {activity[0]}, Title: {activity[1]}")
                    st.write(f"Description: {activity[3]}")
                    st.write(f"Supplies: {activity[4]}")
                    st.write(f"Instructions: {activity[5]}")
                    st.write(f"Source: {activity[6]}")
                    
                    # Use session state to store and retrieve checkbox states
                    activity_id = activity[0]
                    if activity_id not in st.session_state.todo_states:
                        st.session_state.todo_states[activity_id] = activity[7]
                    
                    st.session_state.todo_states[activity_id] = st.checkbox(
                        "To Do",
                        value=st.session_state.todo_states[activity_id],
                        key=f"todo_{activity_id}"
                    )
                    st.write("-----")
            else:
                st.write(f"No matching {activity_type} activities found in the database.")
        else:
            st.write(f"No matching {activity_type} activities found in Pinecone.")

    # Add "Update To Do List" button after displaying all activities
    if st.button("Update To Do List"):
        update_multiple_activities(st.session_state.todo_states)
        st.success("To Do list updated successfully!")
        st.rerun()

elif search_button:
    st.write("Please enter a theme description to search.")
