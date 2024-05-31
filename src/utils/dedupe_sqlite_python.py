import sqlite3
import spacy
import logging
import numpy as np
import pickle
import csv

# Load the spaCy English model with word embeddings
print("Loading spaCy English model...")
nlp = spacy.load("en_core_web_lg")

def normalize_text(text):
    # Process the text using spaCy
    doc = nlp(text)
    # Normalize the text by converting to lowercase and removing punctuation
    normalized_text = " ".join([token.text.lower() for token in doc if not token.is_punct])
    return normalized_text

def precompute_vectors(texts):
    vectors = []
    for text in texts:
        doc = nlp(text)
        if doc.vector_norm > 0:
            vectors.append(doc.vector)
        else:
            vectors.append(None)
    return vectors

def serialize_vector(vector):
    return pickle.dumps(vector) if vector is not None else None

def deserialize_vector(blob):
    return pickle.loads(blob) if blob is not None else None

def semantic_similarity(vec1_blob, vec2_blob):
    try:
        vec1 = deserialize_vector(vec1_blob)
        vec2 = deserialize_vector(vec2_blob)
        if vec1 is None or vec2 is None:
            return 0.0
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        cosine_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(cosine_sim)
    except Exception as e:
        print(f"Error in semantic_similarity function: {str(e)}")
        print(f"vec1: {vec1}")
        print(f"vec2: {vec2}")
        raise e

# Connect to the SQLite database
print("Connecting to the SQLite database...")
conn = sqlite3.connect("activities.db")
cursor = conn.cursor()

# Normalize the text in each field
print("Normalizing text in each field...")
cursor.execute(
    """
    SELECT id, title, description, supplies, instructions
    FROM activities
"""
)
activities = cursor.fetchall()

normalized_activities = []
titles = []
for activity in activities:
    normalized_activity = [activity[0]]  # ID
    normalized_title = normalize_text(activity[1])
    normalized_description = normalize_text(activity[2])
    normalized_supplies = normalize_text(activity[3])
    normalized_instructions = normalize_text(activity[4])
    normalized_activity.extend([normalized_title, normalized_description, normalized_supplies, normalized_instructions])
    titles.append(normalized_title)
    normalized_activities.append(normalized_activity)

# Precompute vectors for titles
print("Precomputing vectors...")
title_vectors = precompute_vectors(titles)

# Create temporary tables for normalized data and vectors
print("Creating temporary tables...")
cursor.execute(
    """
    CREATE TEMPORARY TABLE temp_activities (
        id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        supplies TEXT,
        instructions TEXT,
        title_vector BLOB
    )
"""
)

# Create an index on the temp_activities table
cursor.execute("CREATE INDEX IF NOT EXISTS idx_temp_activities_id ON temp_activities (id)")

data = []
for i, activity in enumerate(normalized_activities):
    data.append(activity + [serialize_vector(title_vectors[i])])

cursor.executemany(
    """
    INSERT INTO temp_activities (id, title, description, supplies, instructions, title_vector)
    VALUES (?, ?, ?, ?, ?, ?)
""",
    data,
)

# Create a custom function for semantic similarity
conn.create_function("semantic_similarity", 2, semantic_similarity)

# Compare fields using semantic similarity
print("Comparing fields using semantic similarity...")
similarity_threshold = 0.8

# Get the total number of activities
cursor.execute("SELECT COUNT(*) FROM temp_activities")
total_activities = cursor.fetchone()[0]

# Set the batch size
batch_size = 25

# Initialize variables for progress tracking
processed_activities = 0
potential_duplicates = []

while processed_activities < total_activities:
    cursor.execute(
        """
        SELECT t1.id AS id1, t2.id AS id2,
               t1.title AS title1, t1.description AS description1, t1.supplies AS supplies1, t1.instructions AS instructions1,
               t2.title AS title2, t2.description AS description2, t2.supplies AS supplies2, t2.instructions AS instructions2,
               semantic_similarity(t1.title_vector, t2.title_vector) AS title_similarity
        FROM temp_activities t1
        JOIN temp_activities t2 ON t1.id < t2.id
        WHERE t1.id BETWEEN ? AND ?
          AND semantic_similarity(t1.title_vector, t2.title_vector) >= ?
    """,
        (
            processed_activities + 1,
            processed_activities + batch_size,
            similarity_threshold,
        ),
    )

    batch_duplicates = cursor.fetchall()
    potential_duplicates.extend(batch_duplicates)

    processed_activities += batch_size
    progress_percentage = (processed_activities / total_activities) * 100
    print(f"Progress: {progress_percentage:.2f}% ({processed_activities}/{total_activities})")

# Display the number of potential duplicates found
num_duplicates = len(potential_duplicates)
print(f"Found {num_duplicates} potential duplicate(s).")

# Open a CSV file for writing the output in the data/ directory
print("Writing potential duplicates to CSV file...")
with open("data/potential_duplicates.csv", "w", newline='') as csvfile:
    fieldnames = ['ID1', 'Title1', 'Description1', 'Supplies1', 'Instructions1', 
                  'ID2', 'Title2', 'Description2', 'Supplies2', 'Instructions2', 'Title Similarity']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for duplicate in potential_duplicates:
        id1, id2, title1, description1, supplies1, instructions1, title2, description2, supplies2, instructions2, title_similarity = duplicate
        writer.writerow({
            'ID1': id1, 'Title1': title1, 'Description1': description1, 'Supplies1': supplies1, 'Instructions1': instructions1,
            'ID2': id2, 'Title2': title2, 'Description2': description2, 'Supplies2': supplies2, 'Instructions2': instructions2,
            'Title Similarity': f"{title_similarity:.2f}"
        })

# Close the database connection
print("Closing the database connection...")
conn.close()

print("Deduplication complete.")
