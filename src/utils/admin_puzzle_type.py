import streamlit as st
import sqlite3
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect('activities.db')
cursor = conn.cursor()

# Streamlit app
st.title('Search Activities by Title')

# User input for keyword
keyword = st.text_input('Enter a keyword to search for activity title:')

if keyword:
    # Query the database
    query = "SELECT * FROM activities WHERE title LIKE ?"
    cursor.execute(query, ('%' + keyword + '%',))
    results = cursor.fetchall()

    # If results are found, display them
    if results:
        df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
        st.write('Results found:')
        st.dataframe(df)

        # Button to change the type field to "Puzzle"
        if st.button('Change type to Puzzle'):
            update_query = "UPDATE activities SET type = 'Puzzle' WHERE title LIKE ?"
            cursor.execute(update_query, ('%' + keyword + '%',))
            conn.commit()
            st.success('Type field updated to "Puzzle" for the selected records.')
    else:
        st.write('No results found.')

# Close the database connection
conn.close()