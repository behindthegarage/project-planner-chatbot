import streamlit as st
import pandas as pd
import sqlite3

# Connect to the SQLite database to fetch records
def fetch_records(sort_by='ID', sort_order='asc'):
    conn = sqlite3.connect('activities.db')
    query = f"SELECT * FROM activities ORDER BY {sort_by} {sort_order}"
    records = pd.read_sql_query(query, conn)
    conn.close()
    return records

# Streamlit app
st.title("Browse Activities Database")

# Sorting options
sort_by = st.selectbox("Sort by:", options=['ID', 'Title', 'Type', 'Duplicate_Status'], index=0)
sort_order = st.selectbox("Sort order:", options=['Ascending', 'Descending'], index=0)
sort_order_sql = 'ASC' if sort_order == 'Ascending' else 'DESC'

# Fetch sorted records
records_df = fetch_records(sort_by, sort_order_sql)

# Display records in a table
st.write("Activities Records:")
st.dataframe(records_df)

# Filtering options
filter_column = st.selectbox("Filter by column:", options=['None'] + list(records_df.columns), index=0)
if filter_column != 'None':
    unique_values = records_df[filter_column].unique()
    selected_value = st.selectbox(f"Select value for {filter_column}:", options=unique_values)
    filtered_df = records_df[records_df[filter_column] == selected_value]
    st.write(f"Filtered Records by {filter_column}:")
    st.dataframe(filtered_df)