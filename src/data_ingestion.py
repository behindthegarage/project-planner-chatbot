import os
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from docx import Document
import json
import hashlib
from text_chunker import tokenize_text, chunk_text, decode_tokens

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize Pinecone
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')
pc = Pinecone(api_key=pinecone_api_key)

# Check if the index exists, if not, create it
if pinecone_index_name not in pc.list_indexes().names():
    pc.create_index(
        name=pinecone_index_name,
        dimension=768,  # Dimension of embeddings from text-embedding-ada-002 model
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-west-2'
        )
    )

index = pc.Index(pinecone_index_name)

def embed_text(text):
    """Embed text using OpenAI's text-embedding-ada-002 model."""
    response = client.embeddings.create(model="text-embedding-ada-002",
    input=text)
    return response.data[0].embedding

def process_docx(file_path):
    """Extract text from a DOCX file, chunk it, and embed it."""
    doc = Document(file_path)
    full_text = ' '.join(para.text.strip() for para in doc.paragraphs if para.text.strip())
    tokens = tokenize_text(full_text)
    chunks = chunk_text(tokens)

    for chunk in chunks:
        decoded_text = decode_tokens(chunk)  # Rename variable here
        embedding = embed_text(decoded_text)
        # Create a unique ID for each chunk
        chunk_id = hashlib.sha256(decoded_text.encode('utf-8')).hexdigest()
        # Correctly pass the chunk_id and embedding as a tuple inside a list
        index.upsert(vectors=[(chunk_id, embedding)])

def process_json(file_path):
    """Extract text from a JSON file, chunk it, and embed it."""
    with open(file_path, 'r') as file:
        data = json.load(file)

    for item in data:
        text = item['body']  # Assuming 'body' contains the text to embed
        tokens = tokenize_text(text)
        chunks = chunk_text(tokens)

        for chunk in chunks:
            decoded_text = decode_tokens(chunk)  # Rename variable here
            embedding = embed_text(decoded_text)
            # Create a unique ID for each chunk
            chunk_id = hashlib.sha256(decoded_text.encode('utf-8')).hexdigest()
            # Correctly pass the chunk_id and embedding as a tuple inside a list
            index.upsert(vectors=[(chunk_id, embedding)])

def main():
    docx_file_path = os.getenv('DOCX_FILE_PATH', '../data/weekly_activities.docx')
    json_file_path = os.getenv('JSON_FILE_PATH', '../data/emails_cleaned.json')
    process_docx(docx_file_path)
    process_json(json_file_path)

if __name__ == "__main__":
    main()

