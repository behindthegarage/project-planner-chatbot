import streamlit as st
import pandas as pd

# Function to read potential duplicates from the file
def read_potential_duplicates(file_path):
    potential_duplicates = []
    with open(file_path, "r") as file:
        lines = file.readlines()
        current_record = {}
        for line in lines:
            if line.startswith("Potential duplicate:"):
                if current_record:
                    # Append the current record to the list and reset for the next record
                    potential_duplicates.append(current_record)
                    current_record = {}
                # Start a new record
                parts = line.strip().split(", ")
                current_record['ID1'] = int(parts[0].split("=")[1])
                current_record['ID2'] = int(parts[1].split("=")[1])
            elif "similarity" in line:
                key, value = line.strip().split(": ")
                current_record[key] = float(value)
        # Append the last record if exists
        if current_record:
            potential_duplicates.append(current_record)

    return potential_duplicates

# Read potential duplicates
file_path = "data/potential_duplicates.txt"
potential_duplicates = read_potential_duplicates(file_path)

# Create a DataFrame for easier manipulation
df = pd.DataFrame(potential_duplicates)

# Streamlit app
st.title("Potential Duplicates Viewer")

# Select a record
selected_id = st.selectbox("Select a record ID to view potential duplicates:", df["ID1"].unique())

# Filter the DataFrame to show only the selected record and its potential duplicates
filtered_df = df[(df["ID1"] == selected_id) | (df["ID2"] == selected_id)]

# Display the selected record and its potential duplicates
st.write(f"Potential duplicates for record ID {selected_id}:")
st.dataframe(filtered_df)
