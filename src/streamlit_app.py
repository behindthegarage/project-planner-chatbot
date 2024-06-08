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

def search_activities(keyword, activity_type, top_k=20):
    """Search for activities based on keyword and optionally filter by type."""
    embedding = get_embedding(keyword)
    query_results = pinecone_index.query(vector=embedding, top_k=top_k, include_metadata=True)
    if activity_type == "All":
        filtered_results = query_results['matches']
    else:
        filtered_results = [result for result in query_results['matches'] if result['metadata']['type'] == activity_type]
    return filtered_results

# Streamlit UI
st.title('Activity Search')
keyword = st.text_input('Enter a keyword or phrase:')
activity_type = st.selectbox('Select Activity Type:', options=['All', 'Art', 'Craft', 'Science', 'Cooking', 'Physical'])

if st.button('Search'):
    if keyword:
        results = search_activities(keyword, activity_type)
        if results:
            activity_ids = [result['id'] for result in results]
            activities = fetch_activities_by_ids(activity_ids)
            if activities:
                for activity, result in zip(activities, results):
                    st.write(f"Pinecone ID: {result['id']}")
                    st.write(f"ID: {activity[0]}, Title: {activity[1]}, Type: {activity[2]}")
                    st.write(f"Description: {activity[3]}")
                    st.write(f"Supplies: {activity[4]}")
                    st.write(f"Instructions: {activity[5]}")
                    st.write(f"Source: {activity[6]}")
                    st.write("-----")
            else:
                st.write("No matching activities found in the database.")
        else:
            st.write("No matching activities found in Pinecone.")
    else:
        st.write("Please enter a keyword to search.")