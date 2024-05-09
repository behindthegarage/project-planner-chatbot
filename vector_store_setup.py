import json
from langchain.chains import LocalChain
from langchain.schema import TextSchema
from langchain.stores import WeaviateStore

def load_data(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def initialize_vector_store():
    vector_store = WeaviateStore()
    return LocalChain(vector_store=vector_store)

def store_emails(chain, emails):
    email_schema = TextSchema(text_field="body")
    for email in emails:
        chain.add_document(email, schema=email_schema)

def setup_vector_store(filepath):
    emails = load_data(filepath)
    chain = initialize_vector_store()
    store_emails(chain, emails)
    print("Data has been chunked and stored successfully.")

