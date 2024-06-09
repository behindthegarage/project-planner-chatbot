import streamlit as st
import sqlite3

# Function to fetch activities that need to be done
def get_todo_activities():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM activities WHERE to_do = 1')
    activities = cursor.fetchall()
    conn.close()
    return activities

# Streamlit App
st.title("Activities To Do")

todo_activities = get_todo_activities()
if todo_activities:
    for activity in todo_activities:
        st.write(f"**{activity[1]}**")  # Title
        st.write(f"Type: {activity[2]}")  # Type
        st.write(f"Description: {activity[3]}")  # Description
        st.write(f"Supplies: {activity[4]}")  # Supplies
        st.write(f"Instructions: {activity[5]}")  # Instructions
        st.write(f"Source: {activity[6]}")  # Source
        st.write("---")
else:
    st.write("No activities to do!")