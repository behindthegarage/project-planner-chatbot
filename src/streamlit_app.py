import sqlite3
import pandas as pd
import streamlit as st

def get_activities():
    # Connect to the SQLite database
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    
    # Execute a query to retrieve all records from the activities table
    cursor.execute('SELECT * FROM activities')
    
    # Fetch all results from the executed query
    activities = cursor.fetchall()
    
    # Fetch column names
    column_names = [description[0] for description in cursor.description]
    
    # Close the database connection
    conn.close()
    
    return column_names, activities

def main():
    st.title("Activities Browser")
    
    # Get activities from the database
    column_names, activities = get_activities()
    
    # Convert activities to a DataFrame for better display
    df = pd.DataFrame(activities, columns=column_names)
    
    # Display activities in a table
    if not df.empty:
        st.write(f"Total activities: {len(df)}")
        st.dataframe(df)
        
        # Detailed view for each activity
        for index, row in df.iterrows():
            with st.expander(f"Activity {index + 1}: {row['title']}"):
                st.write(f"**Type:** {row['type']}")
                st.write(f"**Description:** {row['description']}")
                st.write(f"**Supplies:** {row['supplies']}")
                st.write(f"**Instructions:** {row['instructions']}")
    else:
        st.write("No activities found in the database.")

if __name__ == "__main__":
    main()