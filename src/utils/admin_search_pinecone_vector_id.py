import streamlit as st
import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Pinecone client
pinecone_client = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
pinecone_index = pinecone_client.Index(os.getenv('PINECONE_INDEX_NAME'))

# Streamlit app
st.title('Search Pinecone Vector Store by ID')

# User input for vector ID
vector_id = st.text_input('Enter the vector ID to search:')

if st.button('Search'):
    if vector_id:
        # Query Pinecone for the vector with the given ID
        try:
            result = pinecone_index.fetch(ids=[vector_id])
            if result and 'vectors' in result and vector_id in result['vectors']:
                vector_data = result['vectors'][vector_id]
                st.write(f"Vector ID: {vector_id}")
                st.write(f"Values: {vector_data['values']}")
                st.write(f"Metadata: {vector_data['metadata']}")
            else:
                st.write('No vector found with the given ID.')
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.write('Please enter a vector ID.')