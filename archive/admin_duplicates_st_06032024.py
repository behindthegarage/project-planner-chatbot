import streamlit as st
import pandas as pd
import csv
import sqlite3
# import utils.dedupe_sqlite_python

# Function to read potential duplicates from the file
def read_potential_duplicates(file_path):
    potential_duplicates = []
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            id1 = int(row['ID1'])
            title1 = row['Title1']
            description1 = row['Description1']
            supplies1 = row['Supplies1']
            instructions1 = row['Instructions1']
            id2 = int(row['ID2'])
            title2 = row['Title2']
            description2 = row['Description2']
            supplies2 = row['Supplies2']
            instructions2 = row['Instructions2']
            title_similarity = float(row['Title Similarity'])
            potential_duplicates.append((id1, title1, description1, supplies1, instructions1, id2, title2, description2, supplies2, instructions2, title_similarity))
    return potential_duplicates

# Function to write potential duplicates to the file
def write_potential_duplicates(file_path, potential_duplicates):
    with open(file_path, "w", newline='') as csvfile:
        fieldnames = ['ID1', 'Title1', 'Description1', 'Supplies1', 'Instructions1', 
                      'ID2', 'Title2', 'Description2', 'Supplies2', 'Instructions2', 'Title Similarity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for duplicate in potential_duplicates:
            writer.writerow({
                'ID1': duplicate[0], 'Title1': duplicate[1], 'Description1': duplicate[2], 'Supplies1': duplicate[3], 'Instructions1': duplicate[4],
                'ID2': duplicate[5], 'Title2': duplicate[6], 'Description2': duplicate[7], 'Supplies2': duplicate[8], 'Instructions2': duplicate[9],
                'Title Similarity': f"{duplicate[10]:.2f}"
            })

# Read potential duplicates
file_path = "data/potential_duplicates.csv"
potential_duplicates = read_potential_duplicates(file_path)

# Create a DataFrame for easier manipulation
df = pd.DataFrame(potential_duplicates, columns=["ID1", "Title1", "Description1", "Supplies1", "Instructions1", "ID2", "Title2", "Description2", "Supplies2", "Instructions2", "Title Similarity"])

# Streamlit app
st.title("Potential Duplicates Viewer")

# Button to reset potential duplicates
#  if st.button("Start Over"):
        
    # Run dedupe_sqlite_python.py
    # utils.dedupe_sqlite_python.main()
    
    #st.success("Potential duplicates have been reset")
    # Refresh the page to show the updated list
    # st.rerun()

# Select a record
first_selected_id = st.selectbox("Select a record ID to view potential duplicates:", df["ID1"].unique())
selected_id = first_selected_id

# Display an input box to allow the user to enter or change the ID of the selected record
selected_id = st.number_input("Selected Record ID", value=selected_id, step=1)

# Filter the DataFrame to show only the potential duplicates for the selected record
filtered_df = df[df["ID1"] == selected_id][["ID2", "Title2", "Description2", "Supplies2", "Instructions2"]]

# Check if the selected ID exists in the DataFrame
if not filtered_df.empty:
    # Display the potential duplicates for the selected record
    selected_title = df[df["ID1"] == selected_id]["Title1"].iloc[0]
    selected_description = df[df["ID1"] == selected_id]["Description1"].iloc[0]
    selected_supplies = df[df["ID1"] == selected_id]["Supplies1"].iloc[0]
    selected_instructions = df[df["ID1"] == selected_id]["Instructions1"].iloc[0]
    st.write(f"Potential duplicates for record ID {selected_id}: {selected_title} - {selected_description}")
    # st.table(filtered_df)

    # Add checkboxes for each potential duplicate
    selected_duplicates = []
    for index, row in filtered_df.iterrows():
        checkbox = st.checkbox(f"Select duplicate ID2: {row['ID2']}: {row['Title2']} - {row['Description2']}", key=f"checkbox_{row.name}")
        if checkbox:
            selected_duplicates.append(row.name)

    # Button to delete selected duplicates
    if st.button("Delete Selected Duplicates"):
        # Get the IDs of the selected duplicates
        selected_duplicate_ids = filtered_df.loc[selected_duplicates, "ID2"].tolist()
        
        # Connect to the SQLite database
        conn = sqlite3.connect('activities.db')
        cursor = conn.cursor()
        
        # Delete the selected duplicates from the database
        for duplicate_id in selected_duplicate_ids:
            cursor.execute("DELETE FROM activities WHERE ID = ?", (duplicate_id,))
            st.write(f"Deleted record with ID: {duplicate_id}")
        
        # Commit the changes and close the database connection
        conn.commit()
        conn.close()
        
        # Remove the selected duplicates from the potential_duplicates list
        potential_duplicates = [dup for dup in potential_duplicates if dup[5] not in selected_duplicate_ids]
        
        # Write the updated list back to the CSV file
        write_potential_duplicates(file_path, potential_duplicates)
        
        st.success("Selected duplicates have been deleted.")
        # Refresh the page to show the updated list
        st.rerun()
else:
    st.write(f"No potential duplicates found for record ID {selected_id}.")

# Connect to the SQLite database to fetch records
conn = sqlite3.connect('activities.db')
cursor = conn.cursor()
# Execute the query to fetch all records
cursor.execute("SELECT * FROM activities")
records = cursor.fetchall()
# Close the database connection
conn.close()

# Convert the fetched records into a DataFrame for display
records_df = pd.DataFrame(records, columns=['ID', 'Title', 'Type', 'Description', 'Supplies', 'Instructions', 'Source', 'Duplicates'])
# Display the records in a table using Streamlit
st.write("Viewing all records in activities database:")
st.dataframe(records_df)