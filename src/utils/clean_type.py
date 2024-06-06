import os
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

def analyze_activity(title, description, supplies):
    prompt = f"""
    Given the following activity details:

    Title: {title}
    Description: {description}
    Supplies: {supplies}

    What is the most accurate category for this activity? Choose from 'Art', 'Craft', 'Science', 'Cooking', or 'Physical'. Respond only with the word of the type chosen. Do not provide any reasoning or added text.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
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

def update_activity_type(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, supplies FROM activities WHERE type NOT IN ('Art', 'Craft', 'Science', 'Cooking', 'Physical')")
    activities = cursor.fetchall()

    for activity in activities:
        activity_id, title, description, supplies = activity
        print(f"Processing Activity ID: {activity_id}, Title: {title}")
        new_type = analyze_activity(title, description, supplies)
        print(f"Activity ID: {activity_id}, Title: {title}, Proposed New Type: {new_type}")
        if new_type in ['Art', 'Craft', 'Science', 'Cooking', 'Physical']:
            cursor.execute("UPDATE activities SET type = ? WHERE id = ?", (new_type, activity_id))
            conn.commit()  # Commit changes immediately to ensure data integrity
            print(f"Updated Activity ID: {activity_id}, Title: {title}, New Type: {new_type}")
        else:
            print(f"No update needed for Activity ID: {activity_id}, Title: {title}, as the proposed type '{new_type}' is not valid.")

def main():
    # Connect to the database
    conn = sqlite3.connect('activities.db')
    
    # Update activity types
    update_activity_type(conn)
    
    # Close the database connection
    conn.close()
    print("Activity types updated successfully.")

if __name__ == "__main__":
    main()