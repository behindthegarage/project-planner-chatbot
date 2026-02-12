import os
import sqlite3
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

def compare_activities(activity1, activity2):
    prompt = f"""
    Compare the following two activities and determine if they are duplicates:

    Activity 1:
    Title: {activity1['title']}
    Description: {activity1['description']}
    Supplies: {activity1['supplies']}

    Activity 2:
    Title: {activity2['title']}
    Description: {activity2['description']}
    Supplies: {activity2['supplies']}

    Respond with 'Duplicate' if they are duplicates, otherwise respond with 'Unique'.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        n=1,
        stop=None,
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    api_response_content = response.choices[0].message.content.strip()
    print("API Response Content:", api_response_content)

    return api_response_content

def fetch_activities(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, supplies FROM activities")
    activities = cursor.fetchall()
    return [
        {
            'id': activity[0],
            'title': activity[1],
            'description': activity[2],
            'supplies': activity[3]
        }
        for activity in activities
    ]

def find_duplicates(conn):
    activities = fetch_activities(conn)
    duplicates = []

    for i in range(len(activities)):
        for j in range(i + 1, len(activities)):
            result = compare_activities(activities[i], activities[j])
            if result == 'Duplicate':
                duplicates.append((activities[i], activities[j]))
                print(f"Found duplicate: Activity {activities[i]['id']} and Activity {activities[j]['id']}")

    return duplicates

def delete_activities(conn, activity_ids):
    cursor = conn.cursor()
    cursor.executemany("DELETE FROM activities WHERE id = ?", [(activity_id,) for activity_id in activity_ids])
    conn.commit()

def main():
    st.title("Activity Duplicate Finder")

    # Connect to the database
    conn = sqlite3.connect('activities.db')
    
    # Find duplicates
    duplicates = find_duplicates(conn)
    
    if duplicates:
        st.write("Potential duplicates found:")
        delete_ids = []
        for dup in duplicates:
            activity1, activity2 = dup
            st.write(f"**Activity 1 (ID: {activity1['id']})**")
            st.write(f"Title: {activity1['title']}")
            st.write(f"Description: {activity1['description']}")
            st.write(f"Supplies: {activity1['supplies']}")
            st.write(f"**Activity 2 (ID: {activity2['id']})**")
            st.write(f"Title: {activity2['title']}")
            st.write(f"Description: {activity2['description']}")
            st.write(f"Supplies: {activity2['supplies']}")
            if st.checkbox(f"Delete Activity 1 (ID: {activity1['id']})"):
                delete_ids.append(activity1['id'])
            if st.checkbox(f"Delete Activity 2 (ID: {activity2['id']})"):
                delete_ids.append(activity2['id'])
            st.write("---")
        
        if st.button("Delete Selected Activities"):
            delete_activities(conn, delete_ids)
            st.write("Selected activities have been deleted.")
    else:
        st.write("No duplicates found.")
    
    # Close the database connection
    conn.close()

if __name__ == "__main__":
    main()