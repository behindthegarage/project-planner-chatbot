import sqlite3
import re

def normalize_text(text):
    # Convert text to lowercase
    text = text.lower()
    # Remove punctuation and special characters
    text = re.sub(r'[^\w\s]', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def tokenize_text(text):
    # Split text into individual words
    tokens = text.split()
    return ' '.join(tokens)

def jaccard_similarity(set1, set2):
    set1 = set(set1.split())
    set2 = set(set2.split())
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    if union == 0:
        return 0
    return intersection / union

# Connect to the SQLite database
conn = sqlite3.connect('activities.db')
cursor = conn.cursor()

# Create a custom function for Jaccard similarity
conn.create_function("jaccard_similarity", 2, jaccard_similarity)

# Normalize and tokenize the text in each field
cursor.execute('''
    SELECT id, title, description, supplies, instructions
    FROM activities
''')
activities = cursor.fetchall()

normalized_activities = []
for activity in activities:
    normalized_activity = [activity[0]]  # ID
    for field in activity[1:]:
        normalized_field = normalize_text(field)
        tokenized_field = tokenize_text(normalized_field)
        normalized_activity.append(tokenized_field)
    normalized_activities.append(normalized_activity)

# Create temporary tables for normalized and tokenized data
cursor.execute('''
    CREATE TEMPORARY TABLE temp_activities (
        id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        supplies TEXT,
        instructions TEXT
    )
''')

cursor.executemany('''
    INSERT INTO temp_activities (id, title, description, supplies, instructions)
    VALUES (?, ?, ?, ?, ?)
''', normalized_activities)

# Compare fields using Jaccard similarity
similarity_threshold = 0.7
cursor.execute('''
    SELECT t1.id AS id1, t2.id AS id2,
           jaccard_similarity(t1.title, t2.title) AS title_similarity,
           jaccard_similarity(t1.description, t2.description) AS description_similarity,
           jaccard_similarity(t1.supplies, t2.supplies) AS supplies_similarity,
           jaccard_similarity(t1.instructions, t2.instructions) AS instructions_similarity
    FROM temp_activities t1
    JOIN temp_activities t2 ON t1.id < t2.id
    WHERE jaccard_similarity(t1.title, t2.title) >= ?
       OR jaccard_similarity(t1.description, t2.description) >= ?
       OR jaccard_similarity(t1.supplies, t2.supplies) >= ?
       OR jaccard_similarity(t1.instructions, t2.instructions) >= ?
''', (similarity_threshold, similarity_threshold, similarity_threshold, similarity_threshold))

# Fetch the potential duplicates
potential_duplicates = cursor.fetchall()

# Open a file for writing the output
with open('potential_duplicates.txt', 'w') as file:
    # Print the potential duplicates and save to file
    for duplicate in potential_duplicates:
        output = f"Potential duplicate: ID1={duplicate[0]}, ID2={duplicate[1]}\n"
        output += f"Title similarity: {duplicate[2]}\n"
        output += f"Description similarity: {duplicate[3]}\n"
        output += f"Supplies similarity: {duplicate[4]}\n"
        output += f"Instructions similarity: {duplicate[5]}\n"
        output += "---\n"
        
        print(output)
        file.write(output)

# Close the database connection
conn.close()