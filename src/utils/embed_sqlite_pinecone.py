import os
import sqlite3
import openai
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API keys and index name from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')

if not openai_api_key or not pinecone_api_key or not pinecone_index_name:
    raise ValueError("OPENAI_API_KEY, PINECONE_API_KEY, and PINECONE_INDEX_NAME must be set in the environment variables.")

# Initialize OpenAI
openai.api_key = openai_api_key

# Initialize Pinecone
pc = Pinecone(api_key=pinecone_api_key)

# Create the Pinecone index if it doesn't exist
if pinecone_index_name not in pc.list_indexes().names():
    pc.create_index(
        name=pinecone_index_name,
        dimension=1536,  # Assuming the embedding dimension is 1536
        metric="cosine",
        spec=ServerlessSpec(
            cloud='aws',
            region='us-west-2'
        )
    )

# Connect to the Pinecone index
index = pc.Index(pinecone_index_name)

def fetch_activities(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, type, description, supplies, instructions, source FROM activities")
    activities = cursor.fetchall()
    return [
        {
            'id': activity[0],
            'title': activity[1],
            'type': activity[2],
            'description': activity[3],
            'supplies': activity[4],
            'instructions': activity[5],
            'source': activity[6]
        }
        for activity in activities
    ]

def get_embedding(text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response['data'][0]['embedding']

def embed_activities(conn):
    activities = fetch_activities(conn)
    for activity in activities:
        text = (
            f"Title: {activity['title']}\n"
            f"Type: {activity['type']}\n"
            f"Description: {activity['description']}\n"
            f"Supplies: {activity['supplies']}\n"
            f"Instructions: {activity['instructions']}\n"
            f"Source: {activity['source']}"
        )
        embedding = get_embedding(text)
        index.upsert(vectors=[{"id": str(activity['id']), "values": embedding}])
        print(f"Embedded and upserted activity ID {activity['id']}")
    print(f"Total activities embedded and upserted: {len(activities)}")

def main():
    # Connect to the database
    conn = sqlite3.connect('activities.db')
    
    # Embed activities and store in Pinecone
    embed_activities(conn)
    
    # Close the database connection
    conn.close()
    print("Activities embedded and stored in Pinecone successfully.")

if __name__ == "__main__":
    main()