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

# Sort records alphabetically by title
records_df = records_df.sort_values(by='Title')

# Streamlit app
st.title("Delete Records")

# Display the number of records
st.write(f"Number of records: {len(records_df)}")

# Pagination
records_per_page = 100
total_pages = (len(records_df) - 1) // records_per_page + 1
page = st.selectbox("Page", options=list(range(1, total_pages + 1)), index=0)

# Display records for the current page
start_idx = (page - 1) * records_per_page
end_idx = start_idx + records_per_page
current_records_df = records_df.iloc[start_idx:end_idx]

if not current_records_df.empty:
    st.write("All Records:")
    selected_ids = []
    for index, row in current_records_df.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            checkbox = st.checkbox(f"Select ID: {row['ID']}: **{row['Title']}** - {row['Description']}", key=f"checkbox_{row['ID']}")
        with col2:
            st.write(f"Status: {row['Duplicate_Status']}")
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
    st.write("No records found.")