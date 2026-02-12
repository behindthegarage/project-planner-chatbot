import sqlite3
import json

def create_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            type TEXT,
            description TEXT,
            supplies TEXT,
            instructions TEXT,
            source TEXT
        )
    ''')
    conn.commit()
    return conn

def load_activities_from_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def convert_list_to_string(value):
    if isinstance(value, list):
        return ', '.join(str(item) if not isinstance(item, dict) else json.dumps(item) for item in value)
    elif value is None:
        return ''
    return value

def insert_activities_into_db(conn, activities):
    cursor = conn.cursor()
    for activity in activities:
        title = convert_list_to_string(activity.get('Activity Title'))
        type_ = convert_list_to_string(activity.get('Type'))
        description = convert_list_to_string(activity.get('Description'))
        supplies = convert_list_to_string(activity.get('Supplies'))
        instructions = convert_list_to_string(activity.get('Instructions'))
        
        cursor.execute('''
            INSERT INTO activities (title, type, description, supplies, instructions, source)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            title,
            type_,
            description,
            supplies,
            instructions,
            'Google'  # Set the source to 'Google'
        ))
    conn.commit()

def main():
    # Create or connect to the database
    conn = create_database()
    
    # Load activities from JSON file
    activities = load_activities_from_json('data/google_activities.json')
    
    # Insert activities into the database
    insert_activities_into_db(conn, activities)
    
    # Close the database connection
    conn.close()
    print("Activities added to the database successfully.")

if __name__ == "__main__":
    main()