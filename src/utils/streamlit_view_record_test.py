import streamlit as st
import sqlite3
import pandas as pd

def get_activities(limit=12):
    conn = sqlite3.connect('activities.db')
    query = f"SELECT * FROM activities LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def main():
    st.title("Activities Database Viewer")
    st.write("Displaying the first 12 records from activities.db")

    # Fetch the activities
    activities_df = get_activities()

    # Display the dataframe
    st.dataframe(activities_df)

    # Display individual records with all fields
    for index, row in activities_df.iterrows():
        with st.expander(f"Activity {index + 1}: {row['title']}"):
            for column in activities_df.columns:
                st.write(f"**{column}:** {row[column]}")
            st.write("---")

if __name__ == "__main__":
    main()
