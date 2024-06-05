import os
import sqlite3
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

# Get API keys and index name from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')

if not openai_api_key or not pinecone_api_key or not pinecone_index_name:
    raise ValueError("OPENAI_API_KEY, PINECONE_API_KEY, and PINECONE_INDEX_NAME must be set in the environment variables.")

# Initialize OpenAI

# Initialize Pinecone
pc = Pinecone(api_key=pinecone_api_key)

# Connect to the Pinecone index
index = pc.Index(pinecone_index_name)

def get_embedding(text):
    response = client.embeddings.create(input=text,
    model="text-embedding-3-large")
    return response.data[0].embedding

def search_activities(keyword, top_k=10):
    # Embed the keyword
    keyword_embedding = get_embedding(keyword)

    # Perform similarity search
    results = index.query(
        vector=keyword_embedding,
        top_k=top_k,
        include_metadata=True
    )

    # Print the top results
    print(f"Top {top_k} results for keyword '{keyword}':")
    for i, result in enumerate(results.matches, start=1):
        print(f"{i}. Activity ID: {result.id}, Score: {result.score}")
        print(f"   Metadata: {result.metadata}")
        print()

    return [match.id for match in results.matches]

def get_activity_data(conn, activity_ids):
    cursor = conn.cursor()
    activity_data = []

    for activity_id in activity_ids:
        cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
        activity = cursor.fetchone()
        if activity:
            activity_data.append(activity)

    return activity_data

def print_activity_data(activity_data):
    for activity in activity_data:
        print(f"Activity ID: {activity[0]}")
        print(f"Title: {activity[1]}")
        print(f"Type: {activity[2]}")
        print(f"Description: {activity[3]}")
        print(f"Supplies: {activity[4]}")
        print(f"Instructions: {activity[5]}")
        print(f"Source: {activity[6]}")
        print()

def main():
    # Get keyword input from the user
    keyword = input("Enter a keyword to search for activities: ")

    # Perform similarity search and get activity IDs
    activity_ids = search_activities(keyword)

    # Connect to the database
    conn = sqlite3.connect('activities.db')

    # Retrieve activity data from the database
    activity_data = get_activity_data(conn, activity_ids)

    # Print the activity data
    print_activity_data(activity_data)

    # Close the database connection
    conn.close()

if __name__ == "__main__":
    main()