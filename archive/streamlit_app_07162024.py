import streamlit as st
import sqlite3
import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Pinecone
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')

if not pinecone_api_key or not pinecone_index_name:
    raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_NAME must be set in the environment variables.")

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index(pinecone_index_name)

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

# Function to fetch all activities from the database
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

# Function to delete an activity from the database and Pinecone
def delete_activity(id):
    # Delete from SQLite database
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM activities WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    # Delete from Pinecone
    index.delete(ids=[str(id)])

# Streamlit App
st.title("Summer Camp Activities")

menu = ["Add Activity", "View Activities", "Edit Activity", "Delete Activity", "View To Do Activities", "View Supplies List"]
choice = st.sidebar.selectbox("Menu", menu, key="main_menu")

if choice == "Add Activity":
    st.subheader("Add New Activity")
    title = st.text_input("Title", key="add_title")
    type = st.selectbox("Type", ["Art", "Cooking", "Craft", "Group Game", "Physical", "Puzzle", "Science"], key="add_type")
    description = st.text_area("Description", key="add_description")
    supplies = st.text_area("Supplies", key="add_supplies")
    instructions = st.text_area("Instructions", key="add_instructions")
    source = st.text_input("Source", key="add_source")
    to_do = st.checkbox("To Do", key="add_to_do")
    
    if st.button("Add", key="add_button"):
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
    selected_id = st.selectbox("Select Activity ID", activity_ids, key="edit_select_id")
    
    if selected_id:
        activity = [a for a in activities if a[0] == selected_id][0]
        title = st.text_input("Title", activity[1], key="edit_title")
        type = st.selectbox("Type", ["Art", "Cooking", "Craft", "Group Game", "Physical", "Puzzle", "Science"], index=["Art", "Cooking", "Craft", "Group Game", "Physical", "Puzzle", "Science"].index(activity[2]), key="edit_type")
        description = st.text_area("Description", activity[3], key="edit_description")
        supplies = st.text_area("Supplies", activity[4], key="edit_supplies")
        instructions = st.text_area("Instructions", activity[5], key="edit_instructions")
        source = st.text_input("Source", activity[6], key="edit_source")
        to_do = st.checkbox("To Do", activity[7], key="edit_to_do")
        
        if st.button("Update", key="edit_button"):
            update_activity(selected_id, title, type, description, supplies, instructions, source, to_do)
            st.success(f"Activity '{title}' updated successfully!")

elif choice == "Delete Activity":
    st.subheader("Delete Activity")
    activities = get_activities()
    activity_ids = [activity[0] for activity in activities]
    selected_id = st.selectbox("Select Activity ID", activity_ids, key="delete_select_id")
    
    if selected_id and st.button("Delete", key="delete_button"):
        delete_activity(selected_id)
        st.success("Activity deleted successfully from both SQLite and Pinecone!")

elif choice == "View To Do Activities":
    st.subheader("To Do Activities")
    todo_activities = get_todo_activities()
    if todo_activities:
        for activity in todo_activities:
            st.write(f"**{activity[1]}**")  # Title
            st.write(f"ID: {activity[0]}")  # ID
            st.write(f"Type: {activity[2]}")  # Type
            st.write(f"Description: {activity[3]}")  # Description
            st.write(f"Supplies: {activity[4]}")  # Supplies
            st.write(f"Instructions: {activity[5]}")  # Instructions
            st.write(f"Source: {activity[6]}")  # Source
            to_do = st.checkbox("To Do", value=activity[7], key=f"todo_{activity[0]}")

            if to_do != activity[7]:
                update_activity(activity[0], activity[1], activity[2], activity[3], activity[4], activity[5], activity[6], to_do)
                st.rerun()
            st.write("---")
    else:
        st.write("No activities to do!")

elif choice == "View Supplies List":
    st.subheader("Supplies List for All To Do Activities")
    supplies_list = get_supplies_list()
    if supplies_list:
        supplies_container = st.container()
        with supplies_container:
            for supplies in supplies_list:
                items = supplies[0].split(',')  # Assuming supplies are comma-separated
                for item in items:
                    st.write(f"- {item.strip()}")
        
        if st.button("Print Supplies List"):
            printable_supplies = ''
            for supplies in supplies_list:
                items = supplies[0].split(',')
                for item in items:
                    printable_supplies += f"- {item.strip()}<br>"
            
            st.markdown(f'''
                <div style="display: none;">
                    <div id="printable-supplies">
                        <h2>Supplies List for All To Do Activities</h2>
                        {printable_supplies}
                    </div>
                </div>
                <script>
                    var printContents = document.getElementById("printable-supplies").innerHTML;
                    var originalContents = document.body.innerHTML;
                    document.body.innerHTML = printContents;
                    window.print();
                    document.body.innerHTML = originalContents;
                </script>
            ''', unsafe_allow_html=True)
    else:
        st.write("No supplies needed for the activities!")