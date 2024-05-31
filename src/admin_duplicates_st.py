import streamlit as st
import pandas as pd
import csv

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

# Select a record
selected_id = st.selectbox("Select a record ID to view potential duplicates:", df["ID1"].unique())

# Filter the DataFrame to show only the potential duplicates for the selected record
filtered_df = df[(df["ID1"] == selected_id) | (df["ID2"] == selected_id)]
filtered_df = filtered_df[(filtered_df["ID1"] != selected_id) & (filtered_df["ID2"] != selected_id)]

# Display the potential duplicates for the selected record
st.write(f"Potential duplicates for record ID {selected_id}:")
st.dataframe(filtered_df)

# Add checkboxes for each potential duplicate
selected_duplicates = []
for index, row in filtered_df.iterrows():
    checkbox = st.checkbox(f"Select duplicate pair (ID1: {row['ID1']}, ID2: {row['ID2']})", key=f"checkbox_{index}")
    if checkbox:
        selected_duplicates.append(index)

# Button to delete selected duplicates
if st.button("Delete Selected Duplicates"):
    # Filter out the selected duplicates
    potential_duplicates = [dup for i, dup in enumerate(potential_duplicates) if i not in selected_duplicates]
    # Write the updated list back to the CSV file
    write_potential_duplicates(file_path, potential_duplicates)
    st.success("Selected duplicates have been deleted.")
    # Refresh the page to show the updated list
    st.experimental_rerun()