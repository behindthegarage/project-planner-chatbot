from openai import OpenAI
import json
import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

# Initialize Pinecone
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')
pc = Pinecone(api_key=pinecone_api_key)

# Connect to the index
index = pc.Index(pinecone_index_name)

def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

config = load_config()

def generate_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response['data'][0]['embedding']

def fetch_similar_data_from_pinecone(query_embedding):
    try:
        # Query Pinecone for similar vectors
        response = index.query(
            vector=query_embedding,
            top_k=10  # Adjust the number of results as needed
        )
        # Extract metadata or other relevant data from the response
        similar_data = [item['metadata'] for item in response['matches']]
        return similar_data
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return []

# Example of using database configuration
database_config = config['database']

def chat_with_openai(prompt, context):
    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": context},
            {"role": "user", "content": prompt}
        ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred while trying to generate a response: {e}")
        return "Sorry, I couldn't generate a response due to an error."

def main():
    print("Welcome to the Project Planner Chatbot. Type 'quit' to exit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("Exiting chat...")
            break

        # Generate embedding for the user's input
        query_embedding = generate_embedding(user_input)

        # Fetch similar data from Pinecone
        similar_data = fetch_similar_data_from_pinecone(query_embedding)
        context = " ".join([item['body'] for item in similar_data])  # Assuming 'body' contains the text

        # Use the context and user input to chat with OpenAI
        response = chat_with_openai(user_input, context)
        print("Chatbot:", response)

if __name__ == "__main__":
    main()