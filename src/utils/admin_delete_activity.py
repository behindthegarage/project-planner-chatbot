import streamlit as st
import sqlite3
import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Pinecone client
pinecone_client = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
pinecone_index = pinecone_client.Index(os.getenv('PINECONE_INDEX_NAME'))

# Connect to the SQLite database
conn = sqlite3.connect('activities.db')
cursor = conn.cursor()

# Streamlit app
st.title('Delete Activity by ID')

# User input for activity ID
activity_id = st.text_input('Enter the activity ID to search:')

if st.button('Search'):
    if activity_id:
        # Query the database
        query = "SELECT * FROM activities WHERE id = ?"
        cursor.execute(query, (activity_id,))
        result = cursor.fetchone()

        # If result is found, display it
        if result:
            st.write(f"ID: {result[0]}, Title: {result[1]}, Type: {result[2]}")
            st.write(f"Description: {result[3]}")
            st.write(f"Supplies: {result[4]}")
            st.write(f"Instructions: {result[5]}")
            st.write(f"Source: {result[6]}")

            # Button to delete the activity
            if st.button('Delete Activity'):
                # Delete from SQLite database
                delete_query = "DELETE FROM activities WHERE id = ?"
                cursor.execute(delete_query, (activity_id,))
                conn.commit()

                # Delete from Pinecone
                pinecone_index.delete(ids=[activity_id])

                st.success('Activity and its corresponding vector store deleted successfully!')
        else:
            st.write('No activity found with the given ID.')
    else:
        st.write('Please enter an activity ID.')

# Close the database connection
conn.close()