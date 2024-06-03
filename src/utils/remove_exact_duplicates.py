import sqlite3

def mark_exact_title_duplicates():
    # Connect to the SQLite database
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()

    # Fetch all records from the activities table
    cursor.execute("SELECT id, title FROM activities")
    records = cursor.fetchall()

    # Create a dictionary to store titles and their corresponding IDs
    title_dict = {}
    for record in records:
        record_id, title = record
        if title in title_dict:
            title_dict[title].append(record_id)
        else:
            title_dict[title] = [record_id]

    # Counter for altered records
    altered_count = 0

    # Identify titles with duplicates and update their duplicate_status to 'C'
    for title, ids in title_dict.items():
        if len(ids) > 1:
            for record_id in ids:
                cursor.execute("UPDATE activities SET duplicate_status = 'C' WHERE id = ?", (record_id,))
                altered_count += 1

    # Commit the changes and close the database connection
    conn.commit()
    conn.close()

    # Display the number of altered records
    print(f"Number of records altered: {altered_count}")

if __name__ == "__main__":
    mark_exact_title_duplicates()