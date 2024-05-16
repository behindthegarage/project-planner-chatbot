import sqlite3
import json

def create_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            type TEXT,
            description TEXT,
            supplies TEXT,
            instructions TEXT
        )
    ''')
    conn.commit()
    return conn

def load_activities_from_json(file_path):
    with open('data/email_activities.json', 'r') as file:
        return json.load(file)

def insert_activities_into_db(conn, activities):
    cursor = conn.cursor()
    for activity in activities:
        cursor.execute('''
            INSERT INTO activities (title, type, description, supplies, instructions)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            activity['Activity Title'],
            activity['Type'],
            activity['Description'],
            ', '.join(activity['Supplies']),
            activity['Instructions']
        ))
    conn.commit()

def main():
    # Create or connect to the database
    conn = create_database()
    
    # Load activities from JSON file
    activities = load_activities_from_json('data/email_activities.json')
    
    # Insert activities into the database
    insert_activities_into_db(conn, activities)
    
    # Close the database connection
    conn.close()
    print("Activities added to the database successfully.")

if __name__ == "__main__":
    main()