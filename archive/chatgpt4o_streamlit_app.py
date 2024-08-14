import streamlit as st
import sqlite3

# Function to fetch activities from the database
def get_activities():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM activities')
    activities = cursor.fetchall()
    conn.close()
    return activities

# Function to add an activity to the database
def add_activity(title, type, description, supplies, instructions, source, to_do):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO activities (title, type, description, supplies, instructions, source, to_do)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, type, description, supplies, instructions, source, to_do))
    conn.commit()
    conn.close()

# Function to update an activity in the database
def update_activity(id, title, type, description, supplies, instructions, source, to_do):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE activities
    SET title = ?, type = ?, description = ?, supplies = ?, instructions = ?, source = ?, to_do = ?
    WHERE id = ?
    ''', (title, type, description, supplies, instructions, source, to_do, id))
    conn.commit()
    conn.close()

# Function to delete an activity from the database
def delete_activity(id):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM activities WHERE id = ?', (id,))
    conn.commit()
    conn.close()

# Streamlit App
st.title("Activities Database")

menu = ["Add Activity", "View Activities", "Edit Activity", "Delete Activity"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Add Activity":
    st.subheader("Add New Activity")
    title = st.text_input("Title")
    type = st.selectbox("Type", ["Art", "Cooking", "Craft", "Group Game", "Physical", "Puzzle", "Science"])
    description = st.text_area("Description")
    supplies = st.text_area("Supplies")
    instructions = st.text_area("Instructions")
    source = st.text_input("Source")
    to_do = st.checkbox("To Do")
    
    if st.button("Add"):
        add_activity(title, type, description, supplies, instructions, source, to_do)
        st.success(f"Activity '{title}' added successfully!")

elif choice == "View Activities":
    st.subheader("All Activities")
    activities = get_activities()
    for activity in activities:
        st.write(f"**{activity[1]}**")
        st.write(f"Type: {activity[2]}")
        st.write(f"Description: {activity[3]}")
        st.write(f"Supplies: {activity[4]}")
        st.write(f"Instructions: {activity[5]}")
        st.write(f"Source: {activity[6]}")
        st.write(f"To Do: {'Yes' if activity[7] else 'No'}")
        st.write("---")

elif choice == "Edit Activity":
    st.subheader("Edit Activity")
    activities = get_activities()
    activity_ids = [activity[0] for activity in activities]
    selected_id = st.selectbox("Select Activity ID", activity_ids)
    
    if selected_id:
        activity = [a for a in activities if a[0] == selected_id][0]
        title = st.text_input("Title", activity[1])
        type = st.selectbox("Type", ["Art", "Cooking", "Craft", "Group Game", "Physical", "Puzzle", "Science"], index=["Art", "Cooking", "Craft", "Group Game", "Physical", "Puzzle", "Science"].index(activity[2]))
        description = st.text_area("Description", activity[3])
        supplies = st.text_area("Supplies", activity[4])
        instructions = st.text_area("Instructions", activity[5])
        source = st.text_input("Source", activity[6])
        to_do = st.checkbox("To Do", activity[7])
        
        if st.button("Update"):
            update_activity(selected_id, title, type, description, supplies, instructions, source, to_do)
            st.success(f"Activity '{title}' updated successfully!")

elif choice == "Delete Activity":
    st.subheader("Delete Activity")
    activities = get_activities()
    activity_ids = [activity[0] for activity in activities]
    selected_id = st.selectbox("Select Activity ID", activity_ids)
    
    if selected_id and st.button("Delete"):
        delete_activity(selected_id)
        st.success("Activity deleted successfully!")