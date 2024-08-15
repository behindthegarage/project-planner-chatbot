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

# Connect to the SQLite database
conn = sqlite3.connect('activities.db')
cursor = conn.cursor()

# Streamlit app
st.title('Add New Activity')

# User input for activity details
title = st.text_input('Title')
type_ = st.text_input('Type')
description = st.text_area('Description')
supplies = st.text_area('Supplies')
instructions = st.text_area('Instructions')

if st.button('Add Activity'):
    if title and type_ and description and supplies and instructions:
        # Insert the new activity into the database
        insert_query = """
        INSERT INTO activities (title, type, description, supplies, instructions)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query, (title, type_, description, supplies, instructions))
        conn.commit()
        
        # Fetch the last inserted activity ID
        activity_id = cursor.lastrowid
        
        print(f"Title: {title}")
        
        # Create a combined text from title, description, supplies, and instructions
        text = (
            f"Title: {title}\n"
            f"Description: {description}\n"
            f"Supplies: {supplies}\n"
            f"Instructions: {instructions}"
        )
        
        # Generate embedding for the combined text
        embedding = get_embedding(text)
        
        # Upsert the embedding into Pinecone with the type as metadata
        index.upsert(vectors=[{
            "id": str(activity_id),
            "values": embedding,
            "metadata": {"type": type_}
        }])
        
        st.success('Activity added and embedded successfully!')
    else:
        st.error('Please fill in all fields.')

# Close the database connection
conn.close()