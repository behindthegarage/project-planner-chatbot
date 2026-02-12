import os
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

def analyze_activity(title, description):
    prompt = f"""
    Given the following activity details:

    Title: {title}
    Description: {description}

    Determine if the activity is more accurately categorized as a 'Field Trip' rather than 'Physical'. 
    Respond with 'Field Trip' if it is more accurate, otherwise respond with 'Physical'.
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

def update_activity_type(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description FROM activities WHERE type = 'Physical'")
    activities = cursor.fetchall()

    for activity in activities:
        activity_id, title, description = activity
        new_type = analyze_activity(title, description)
        if new_type == 'Field Trip':
            cursor.execute("UPDATE activities SET type = ? WHERE id = ?", (new_type, activity_id))
            print(f"Updated activity ID {activity_id} to 'Field Trip'")

    conn.commit()

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