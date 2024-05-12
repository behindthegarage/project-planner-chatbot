import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Pinecone
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')
pc = Pinecone(api_key=pinecone_api_key)

# Connect to the index
index = pc.Index(pinecone_index_name)

# Clear the index by deleting all vectors
index.delete(delete_all=True)
