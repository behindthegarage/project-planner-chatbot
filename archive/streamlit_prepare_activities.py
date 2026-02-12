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

# Function to fetch supplies for all to-do activities
def get_supplies_list():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT supplies FROM activities WHERE to_do = 1')
    supplies = cursor.fetchall()
    conn.close()
    return supplies

# Streamlit App
st.title("Activities To Do")

# Sidebar
option = st.sidebar.radio(
    "Select an option",
    ("View To Do Activities", "View Supplies List")
)

todo_activities = get_todo_activities()

if option == "View To Do Activities":
    if todo_activities:
        for activity in todo_activities:
            st.write(f"**{activity[1]}**")  # Title            
            st.write(f"ID: {activity[0]}")  # ID
            st.write(f"Type: {activity[2]}")  # Type
            st.write(f"Description: {activity[3]}")  # Description
            st.write(f"Supplies: {activity[4]}")  # Supplies
            st.write(f"Instructions: {activity[5]}")  # Instructions
            st.write(f"Source: {activity[6]}")  # Source
            st.write("---")
    else:
        st.write("No activities to do!")
elif option == "View Supplies List":
    supplies_list = get_supplies_list()
    if supplies_list:
        st.write("Supplies List for All To Do Activities:")
        for supplies in supplies_list:
            items = supplies[0].split(',')  # Assuming supplies are comma-separated
            for item in items:
                st.write(f"- {item.strip()}")
    else:
        st.write("No supplies needed for the activities!")