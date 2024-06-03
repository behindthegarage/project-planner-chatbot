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

# Initialize session state
if 'selected_id' not in st.session_state:
    st.session_state.selected_id = int(records_df["ID"].min())

# Streamlit app
st.title("Activities Viewer")

# Select a record
selected_id = st.selectbox(
    "Select a record ID to view related records:",
    records_df["ID"].unique(),
    index=int(records_df[records_df["ID"] == st.session_state.selected_id].index[0])
)

# Display the selected record details
selected_record = records_df[records_df["ID"] == selected_id].iloc[0]
st.write(f"Selected Record: **{selected_record['Title']}** - {selected_record['Description']}")
st.write(f"Duplicate Status: {selected_record['Duplicate_Status']}")

# Get related IDs from the selected record
related_ids = selected_record['Related_IDs']
if related_ids:
    related_ids = list(map(int, related_ids.split(',')))
    related_records_df = records_df[records_df["ID"].isin(related_ids)]
else:
    related_records_df = pd.DataFrame(columns=records_df.columns)

# Display related records
st.write("Related Records:")
selected_related_ids = []
for index, row in related_records_df.iterrows():
    checkbox = st.checkbox(f"Select related ID: {row['ID']}: **{row['Title']}** - {row['Description']} (Duplicate Status: {row['Duplicate_Status']})", key=f"checkbox_{row['ID']}")
    if checkbox:
        selected_related_ids.append(row['ID'])

# Button to mark records
if st.button("Mark Records"):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    
    # Update duplicate_status for the selected record
    # cursor.execute("UPDATE activities SET duplicate_status = 'N' WHERE id = ?", (selected_id,))
    
    # Update duplicate_status for the selected related records
    for related_id in selected_related_ids:
        cursor.execute("UPDATE activities SET duplicate_status = 'C' WHERE id = ?", (related_id,))
    
    # Update duplicate_status for the non-selected related records
    # if related_ids:
        # non_selected_related_ids = set(related_ids) - set(selected_related_ids)
        # for related_id in non_selected_related_ids:
        #      cursor.execute("UPDATE activities SET duplicate_status = 'P' WHERE id = ? AND duplicate_status != 'C'", (related_id,))
    
    # Commit the changes and close the database connection
    conn.commit()
    conn.close()
    
    st.success("Records have been marked.")
    st.rerun()

# Button to go to the next record with numbers in the related_id field and does not have 'C' in the duplicate_status field
if st.button("Next"):
    next_record = records_df[
        (records_df["ID"] > selected_id) & 
        (records_df["Duplicate_Status"] != 'C') & 
        (records_df["Related_IDs"].str.contains(r'\d', na=False))
    ].head(1)
    if not next_record.empty:
        next_id = int(next_record["ID"].values[0])
        st.session_state.selected_id = next_id
        st.rerun()
    else:
        st.warning("No more records with numbers in the related_id field and without 'C' in the duplicate_status field.")

# Display all records in the activities database
st.write("Viewing all records in activities database:")
st.dataframe(records_df)