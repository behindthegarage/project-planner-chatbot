import streamlit as st
import sqlite3
import os
import json
from anthropic import Anthropic
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize clients
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
pinecone_client = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
pinecone_index = pinecone_client.Index(os.getenv('PINECONE_INDEX_NAME'))

# Initialize session state for generated activities
if 'generated_activities' not in st.session_state:
    st.session_state.generated_activities = []

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
    pinecone_index.delete(ids=[str(id)])

# New functions from other files
def generate_activities(theme):
    prompt = f"""
    Given the theme "{theme}", create 3 art, 3 craft, 3 science, 3 cooking, and 3 physical activities for children. For each activity, provide the following details:
    "Activity Title": Create a title for the activity
    "Type": Specify "Art" or "Craft" or "Science" or "Cooking" or "Physical"
    "Description": Write a one sentence description of the activity
    "Supplies": List supplies that may be used for the activity
    "Instructions": Write a set of instructions for the activity
    Output the result as a JSON array, with each activity as a separate object in the array.
    """

    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4000,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )

    api_response_content = response.content[0].text

    try:
        json_start = api_response_content.find("[")
        json_end = api_response_content.rfind("]") + 1
        json_content = api_response_content[json_start:json_end]
        return json.loads(json_content)
    except (json.JSONDecodeError, ValueError) as e:
        st.error(f"Failed to decode JSON from API response. Error: {e}")
        return None

def get_embedding(text):
    response = openai_client.embeddings.create(input=text, model="text-embedding-3-large")
    return response.data[0].embedding

def add_activity(conn, cursor, index, activity):
    insert_query = """
    INSERT INTO activities (title, type, description, supplies, instructions, to_do, source)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(insert_query, (
        activity['Activity Title'],
        activity['Type'],
        activity['Description'],
        ', '.join(activity['Supplies']),
        '\n'.join(activity['Instructions']),
        True,
        "AI"
    ))
    conn.commit()
    
    activity_id = cursor.lastrowid
    
    text = (
        f"Title: {activity['Activity Title']}\n"
        f"Description: {activity['Description']}\n"
        f"Supplies: {', '.join(activity['Supplies'])}\n"
        f"Instructions: {' '.join(activity['Instructions'])}"
    )
    
    embedding = get_embedding(text)
    
    index.upsert(vectors=[{
        "id": str(activity_id),
        "values": embedding,
        "metadata": {
            "type": activity['Type'],
            "to_do": True
        }
    }])

def parse_activities(text):
    activities = []
    current_activity = {}
    current_field = None

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            if current_activity:
                activities.append(current_activity)
                current_activity = {}
            current_field = None
        elif ':' in line:
            key, value = line.split(':', 1)
            key = key.lower()
            if key in ['type', 'description', 'supplies', 'instructions']:
                current_activity[key] = value.strip()
                current_field = key
            elif 'title' not in current_activity:
                current_activity['title'] = line.strip()
        elif 'title' not in current_activity:
            current_activity['title'] = line
        elif current_field:
            current_activity[current_field] += ' ' + line

    if current_activity:
        activities.append(current_activity)

    return activities

def search_activities(keyword, top_k=4):
    embedding = get_embedding(keyword)
    activity_types = ['Art', 'Craft', 'Science', 'Cooking', 'Physical']
    results = {}
    for activity_type in activity_types:
        query_results = pinecone_index.query(vector=embedding, top_k=top_k, filter={"type": activity_type}, include_metadata=True)
        results[activity_type] = [result['id'] for result in query_results['matches']]
    return results

# Streamlit App
st.title("Summer Camp Activities")

menu = ["Add Activity", "View Activities", "Edit Activity", "Delete Activity", "View To Do Activities", "View Supplies List", "Generate Activities", "Bulk Add Activities", "Theme Planning"]
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

elif choice == "Generate Activities":
    st.subheader("Generate Activities")
    theme = st.text_input("Enter a theme for the activities:")

    if st.button("Generate Activities"):
        if theme:
            activities = generate_activities(theme)
            if activities:
                st.session_state.generated_activities = activities
                st.success("Activities generated successfully!")
            else:
                st.error("No activities generated.")
        else:
            st.error("Please enter a theme.")

    if st.session_state.generated_activities:
        for i, activity in enumerate(st.session_state.generated_activities):
            st.subheader(activity["Activity Title"])
            st.write(f"**Type**: {activity['Type']}")
            st.write(f"**Description**: {activity['Description']}")
            st.write("**Supplies**:")
            st.write(", ".join(activity['Supplies']))
            st.write("**Instructions**:")
            st.write("\n".join(activity['Instructions']))
            
            key = f"checkbox_{i}_{activity['Activity Title']}"
            activity['selected'] = st.checkbox("Select this activity", key=key, value=activity.get('selected', False))

        if st.button("Add Selected Activities"):
            selected_activities = [a for a in st.session_state.generated_activities if a.get('selected', False)]
            if selected_activities:
                conn = sqlite3.connect('activities.db')
                cursor = conn.cursor()
                
                success_count = 0
                for activity in selected_activities:
                    try:
                        add_activity(conn, cursor, pinecone_index, activity)
                        success_count += 1
                    except Exception as e:
                        st.error(f"Error adding activity '{activity['Activity Title']}': {str(e)}")
                
                conn.close()
                
                if success_count > 0:
                    st.success(f'{success_count} activities added and embedded successfully!')
                    # Clear the generated activities after successful addition
                    st.session_state.generated_activities = []
                    st.rerun()
                if success_count < len(selected_activities):
                    st.warning(f'{len(selected_activities) - success_count} activities failed to add. Please check the errors above.')
            else:
                st.warning("No activities selected. Please select at least one activity to add.")

elif choice == "Bulk Add Activities":
    st.subheader("Bulk Add Activities")
    activities_input = st.text_area('Enter multiple activities (separate each activity with a blank line)', height=300)

    if st.button('Add Activities'):
        if activities_input:
            activities = parse_activities(activities_input)
            
            conn = sqlite3.connect('activities.db')
            cursor = conn.cursor()
            
            success_count = 0
            for activity in activities:
                try:
                    add_activity(conn, cursor, pinecone_index, activity)
                    success_count += 1
                except ValueError as e:
                    st.error(f"Error adding activity: {str(e)}")
                except Exception as e:
                    st.error(f"Unexpected error adding activity: {str(e)}")
            
            conn.close()
            
            if success_count > 0:
                st.success(f'{success_count} activities added and embedded successfully!')
            if success_count < len(activities):
                st.warning(f'{len(activities) - success_count} activities failed to add. Please check the errors above.')
        else:
            st.error('Please enter at least one activity.')

elif choice == "Theme Planning":
    st.subheader("Theme Planning")
    theme_description = st.text_input('Enter a theme description:')

    if 'theme_search_results' not in st.session_state:
        st.session_state.theme_search_results = {}

    if st.button('Search'):
        if theme_description:
            st.session_state.theme_search_results = search_activities(theme_description)
        else:
            st.error("Please enter a theme description to search.")

    if st.session_state.theme_search_results:
        for activity_type, ids in st.session_state.theme_search_results.items():
            if ids:
                activities = get_activities_by_ids(ids)
                if activities:
                    st.subheader(f"{activity_type} Activities:")
                    for activity in activities:
                        st.write(f"ID: {activity[0]}, Title: {activity[1]}")
                        st.write(f"Description: {activity[3]}")
                        st.write(f"Supplies: {activity[4]}")
                        st.write(f"Instructions: {activity[5]}")
                        st.write(f"Source: {activity[6]}")
                        
                        key = f"todo_{activity[0]}"
                        to_do = st.checkbox("To Do", value=activity[7], key=key)
                        if to_do != activity[7]:
                            update_activity(activity[0], activity[1], activity[2], activity[3], activity[4], activity[5], activity[6], to_do)
                            st.rerun()
                        st.write("-----")
                else:
                    st.write(f"No matching {activity_type} activities found in the database.")
            else:
                st.write(f"No matching {activity_type} activities found in Pinecone.")