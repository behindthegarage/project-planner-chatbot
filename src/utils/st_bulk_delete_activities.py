import streamlit as st
import sqlite3
import os
from typing import List
from pinecone import Pinecone

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

# Connect to SQLite database
conn = sqlite3.connect('activities.db')
cursor = conn.cursor()

def parse_input(input_string: str) -> List[int]:
    """Parse user input and return a list of activity IDs."""
    ids = []
    for item in input_string.split(','):
        item = item.strip()
        if '-' in item:
            start, end = map(int, item.split('-'))
            ids.extend(range(start, end + 1))
        else:
            ids.append(int(item))
    return ids

def delete_from_sqlite(activity_ids: List[int]) -> int:
    """Delete activities from SQLite database."""
    placeholders = ','.join('?' * len(activity_ids))
    cursor.execute(f"DELETE FROM activities WHERE id IN ({placeholders})", activity_ids)
    deleted_count = cursor.rowcount
    conn.commit()
    return deleted_count

def delete_from_pinecone(activity_ids: List[int]) -> int:
    """Delete activities from Pinecone vector database."""
    deleted_count = 0
    for id in activity_ids:
        try:
            index.delete(ids=[str(id)])
            deleted_count += 1
        except Exception as e:
            st.error(f"Error deleting ID {id} from Pinecone: {str(e)}")
    return deleted_count

st.title("Bulk Delete Activities")

input_ids = st.text_input("Enter activity IDs to delete (comma-separated, use hyphens for ranges):")

if st.button("Delete Activities"):
    if input_ids:
        activity_ids = parse_input(input_ids)
        
        sqlite_deleted = delete_from_sqlite(activity_ids)
        pinecone_deleted = delete_from_pinecone(activity_ids)
        
        st.success(f"Deleted {sqlite_deleted} records from SQLite database.")
        st.success(f"Deleted {pinecone_deleted} records from Pinecone vector database.")
        
        if sqlite_deleted != pinecone_deleted:
            st.warning("The number of deleted records in SQLite and Pinecone doesn't match. Some records may not exist in both databases.")
    else:
        st.warning("Please enter activity IDs to delete.")

# Close the database connection when the app is done
conn.close()
