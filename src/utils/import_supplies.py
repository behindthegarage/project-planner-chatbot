import sqlite3
import csv
import os

# Get the current working directory and adjust paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
DB_PATH = os.path.join(project_root, 'activities.db')
CSV_PATH = os.path.join(project_root, 'data', '07082025_supplies.csv')

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS available_supplies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            item TEXT
        )
    ''')
    conn.commit()
    # Clear table before import
    cursor.execute('DELETE FROM available_supplies')
    conn.commit()

def import_csv(conn):
    cursor = conn.cursor()
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                category, item = row[0].strip(), row[1].strip()
                cursor.execute('INSERT INTO available_supplies (category, item) VALUES (?, ?)', (category, item))
    conn.commit()

def main():
    print(f"Database path: {DB_PATH}")
    print(f"CSV path: {CSV_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return
    
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at {CSV_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)
    import_csv(conn)
    conn.close()
    print('Supplies imported successfully.')

if __name__ == '__main__':
    main() 