import streamlit as st
import sqlite3
import streamlit.components.v1 as components

# Function to fetch a specific activity from the database by its ID
def get_activity(activity_id):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM activities WHERE id = ?', (activity_id,))
    activity = cursor.fetchone()
    conn.close()
    return activity

# Function to generate the lesson plan HTML
def generate_lesson_plan_html(activity):
    title, type, description, supplies, instructions, source = activity[1:7]
    supplies_list = supplies.split(',') if supplies else []
    instructions_list = instructions.split('.') if instructions else []
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            .bold {{
                font-weight: bold;
            }}
            .checkbox-container {{
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <h1 class="bold">Summer Lesson Plan</h1>

        <p class="bold">Grade: 4th-7th</p>
        <p>Week #:</p>
        <p>Date:</p>
        <p>Weekly Theme:</p>

        <h2 class="bold">Check one of the following:</h2>
        <div class="checkbox-container">
            <input type="checkbox" id="monday" name="day" value="Monday">
            <label for="monday">Monday (art, science, cooking) PM for K/1, AM for 2-7</label>
        </div>
        <div class="checkbox-container">
            <input type="checkbox" id="tuesday" name="day" value="Tuesday">
            <label for="tuesday">Tuesday Exploratories (educational, creative, active)</label>
        </div>
        <div class="checkbox-container">
            <input type="checkbox" id="wednesday" name="day" value="Wednesday">
            <label for="wednesday">Wednesday No lessons</label>
        </div>
        <div class="checkbox-container">
            <input type="checkbox" id="thursday" name="day" value="Thursday">
            <label for="thursday">Thursday Exploratories (educational, creative, active)</label>
        </div>
        <div class="checkbox-container">
            <input type="checkbox" id="friday" name="day" value="Friday">
            <label for="friday">Friday Exploratories (educational, creative, active)</label>
        </div>

        <h2 class="bold">Name of Lesson: {title}</h2>
        
        <h2 class="bold">Supplies Needed:</h2>
        <ul>
            {''.join([f"<li>{supply}</li>" for supply in supplies_list])}
        </ul>

        <h2 class="bold">Steps to complete lesson/activity/project:</h2>
        <ol>
            {''.join([f"<li>{instruction}</li>" for instruction in instructions_list])}
        </ol>
    </body>
    </html>
    """
    return html

# Streamlit App
st.title("Kids Activities Database")

menu = ["Add Activity", "View Activities", "Edit Activity", "Delete Activity", "Lesson Plan"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Add Activity":
    st.subheader("Add New Activity")
    title = st.text_input("Title")
    type = st.selectbox("Type", ["Indoor", "Outdoor", "Craft", "Game", "Educational"])
    description = st.text_area("Description")
    supplies = st.text_area("Supplies")
    instructions = st.text_area("Instructions")
    source = st.text_input("Source")
    
    if st.button("Add"):
        add_activity(title, type, description, supplies, instructions, source)
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
        st.write("---")

elif choice == "Edit Activity":
    st.subheader("Edit Activity")
    activities = get_activities()
    activity_ids = [activity[0] for activity in activities]
    selected_id = st.selectbox("Select Activity ID", activity_ids)
    
    if selected_id:
        activity = [a for a in activities if a[0] == selected_id][0]
        title = st.text_input("Title", activity[1])
        type = st.selectbox("Type", ["Indoor", "Outdoor", "Craft", "Game", "Educational"], index=["Indoor", "Outdoor", "Craft", "Game", "Educational"].index(activity[2]))
        description = st.text_area("Description", activity[3])
        supplies = st.text_area("Supplies", activity[4])
        instructions = st.text_area("Instructions", activity[5])
        source = st.text_input("Source", activity[6])
        
        if st.button("Update"):
            update_activity(selected_id, title, type, description, supplies, instructions, source)
            st.success(f"Activity '{title}' updated successfully!")

elif choice == "Delete Activity":
    st.subheader("Delete Activity")
    activities = get_activities()
    activity_ids = [activity[0] for activity in activities]
    selected_id = st.selectbox("Select Activity ID", activity_ids)
    
    if selected_id and st.button("Delete"):
        delete_activity(selected_id)
        st.success("Activity deleted successfully!")

elif choice == "Lesson Plan":
    st.subheader("Generate Lesson Plan")
    activity_id = st.number_input("Enter Activity ID", min_value=1)
    
    if st.button("Generate"):
        activity = get_activity(activity_id)
        if activity:
            lesson_plan_html = generate_lesson_plan_html(activity)
            components.html(lesson_plan_html, height=800, scrolling=True)
        else:
            st.error("Activity not found!")
