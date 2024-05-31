import sqlite3
import spacy
import logging

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

def semantic_similarity(vec1, vec2):
    try:
        if vec1 is None or vec2 is None:
            return 0.0
        return nlp.vocab.vectors.cosine_similarity(vec1, vec2)
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
descriptions = []
for activity in activities:
    normalized_activity = [activity[0]]  # ID
    for i, field in enumerate(activity[1:]):
        normalized_field = normalize_text(field)
        normalized_activity.append(normalized_field)
        if i == 0:
            titles.append(normalized_field)
        elif i == 1:
            descriptions.append(normalized_field)
    normalized_activities.append(normalized_activity)

# Precompute vectors for titles and descriptions
print("Precomputing vectors...")
title_vectors = precompute_vectors(titles)
description_vectors = precompute_vectors(descriptions)

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
        title_vector BLOB,
        description_vector BLOB
    )
"""
)

# Create an index on the temp_activities table
cursor.execute("CREATE INDEX IF NOT EXISTS idx_temp_activities_id ON temp_activities (id)")

data = []
for i, activity in enumerate(normalized_activities):
    data.append(activity + [title_vectors[i], description_vectors[i]])

cursor.executemany(
    """
    INSERT INTO temp_activities (id, title, description, supplies, instructions, title_vector, description_vector)
    VALUES (?, ?, ?, ?, ?, ?, ?)
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
               semantic_similarity(t1.title_vector, t2.title_vector) AS title_similarity,
               semantic_similarity(t1.description_vector, t2.description_vector) AS description_similarity
        FROM temp_activities t1
        JOIN temp_activities t2 ON t1.id < t2.id
        WHERE t1.id BETWEEN ? AND ?
          AND (semantic_similarity(t1.title_vector, t2.title_vector) >= ?
               OR semantic_similarity(t1.description_vector, t2.description_vector) >= ?)
    """,
        (
            processed_activities + 1,
            processed_activities + batch_size,
            similarity_threshold,
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

# Open a file for writing the output in the data/ directory
print("Writing potential duplicates to file...")
with open("data/potential_duplicates.txt", "w") as file:
    # Write the number of potential duplicates to the file
    file.write(f"Found {num_duplicates} potential duplicate(s).\n\n")

    # Display the details of each potential duplicate and write to file
    for duplicate in potential_duplicates:
        id1, id2, title_similarity, description_similarity = duplicate

        # Prepare the output string
        output = f"Potential duplicate: ID1={id1}, ID2={id2}\n"
        output += f"  Title similarity: {title_similarity:.2f}\n"
        output += f"  Description similarity: {description_similarity:.2f}\n"
        output += "---\n"

        # Print the output to the console
        print(output)

        # Write the output to the file
        file.write(output)

# Close the database connection
print("Closing the database connection...")
conn.close()

print("Deduplication complete.")