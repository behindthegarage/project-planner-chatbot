import sqlite3
import spacy
import numpy as np
import pickle

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

def update_duplicates_field(conn, potential_duplicates):
    cursor = conn.cursor()

    # Create a dictionary to store the duplicates for each activity
    duplicates_dict = {}
    for duplicate in potential_duplicates:
        id1, id2, _, _, _, _, _, _, _, _, _ = duplicate
        if id1 not in duplicates_dict:
            duplicates_dict[id1] = []
        duplicates_dict[id1].append(id2)

    # Update the "related_ids" field for each activity
    for activity_id, duplicates in duplicates_dict.items():
        duplicates_str = ",".join(str(dup_id) for dup_id in duplicates)
        cursor.execute(
            """
            UPDATE activities
            SET related_ids = ?
            WHERE id = ?
        """,
            (duplicates_str, activity_id),
        )

    conn.commit()

def main():
    # Connect to the SQLite database
    print("Connecting to the SQLite database...")
    conn = sqlite3.connect("activities.db")
    cursor = conn.cursor()

    # Add the "related_ids" field to the activities table if it doesn't exist
    cursor.execute(
        """
        SELECT COUNT(*) 
        FROM pragma_table_info('activities')
        WHERE name = 'related_ids'
    """
    )
    column_exists = cursor.fetchone()[0]

    if not column_exists:
        cursor.execute(
            """
            ALTER TABLE activities
            ADD COLUMN related_ids TEXT
        """
        )
        conn.commit()

    # Normalize the text in each field
    print("Normalizing text in each field...")
    cursor.execute(
        """
        SELECT id, title, description, supplies, instructions
        FROM activities
    """
    )
    activities = cursor.fetchall()

    # ... rest of the code ...

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

    # Update the "related_ids" field in the activities table
    print("Updating the 'related_ids' field in the activities table...")
    update_duplicates_field(conn, potential_duplicates)

    # Close the database connection
    print("Closing the database connection...")
    conn.close()

    print("Deduplication complete.")

if __name__ == "__main__":
    main()