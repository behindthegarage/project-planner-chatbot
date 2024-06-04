import streamlit as st
import pandas as pd
import sqlite3

# Connect to the SQLite database to fetch records
def fetch_records():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities")
    records = cursor.fetchall()
    conn.close()
    return records

# Fetch all records from the activities table
records = fetch_records()

# Convert the fetched records into a DataFrame for display
records_df = pd.DataFrame(records, columns=['ID', 'Title', 'Type', 'Description', 'Supplies', 'Instructions', 'Source', 'Related_IDs', 'Duplicate_Status'])

# Streamlit app
st.title("Delete Records by Title Keyword")

# Input for keyword search
keywords = st.text_input("Enter keywords to search in titles (comma-separated):")

if keywords:
    keyword_list = [kw.strip().lower() for kw in keywords.split(',')]
    
    # Filter records based on keywords
    filtered_records_df = records_df[records_df['Title'].str.lower().str.contains('|'.join(keyword_list))]
    filtered_records_df = filtered_records_df.sort_values(by='Title')
    
    if not filtered_records_df.empty:
        st.write("Search Results:")
        selected_ids = []
        for index, row in filtered_records_df.iterrows():
            checkbox = st.checkbox(f"Select ID: {row['ID']}: **{row['Title']}** - {row['Description']}", key=f"checkbox_{row['ID']}")
            if checkbox:
                selected_ids.append(row['ID'])
        
        # Button to delete selected records
        if st.button("Delete Selected Records"):
            conn = sqlite3.connect('activities.db')
            cursor = conn.cursor()
            
            # Delete selected records
            for record_id in selected_ids:
                cursor.execute("DELETE FROM activities WHERE id = ?", (record_id,))
            
            # Commit the changes and close the database connection
            conn.commit()
            conn.close()
            
            st.success("Selected records have been deleted.")
            st.rerun()
    else:
        st.write("No records found with the given keywords.")
else:
    st.write("Please enter keywords to search.")