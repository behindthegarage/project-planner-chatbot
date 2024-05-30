import sqlite3
import spacy

# Load the spaCy English model with word embeddings
nlp = spacy.load("en_core_web_md")

def normalize_text(text):
    # Process the text using spaCy
    doc = nlp(text)
    # Normalize the text by converting to lowercase and removing punctuation
    normalized_text = " ".join([token.text.lower() for token in doc if not token.is_punct])
    return normalized_text

def semantic_similarity(text1, text2):
    # Process the texts using spaCy
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    # Calculate the semantic similarity using spaCy's word embeddings
    similarity = doc1.similarity(doc2)
    return similarity

# Connect to the SQLite database
conn = sqlite3.connect("activities.db")
cursor = conn.cursor()

# Create a custom function for semantic similarity
conn.create_function("semantic_similarity", 2, semantic_similarity)

# Normalize the text in each field
cursor.execute(
    """
    SELECT id, title, description, supplies, instructions
    FROM activities
"""
)
activities = cursor.fetchall()

normalized_activities = []
for activity in activities:
    normalized_activity = [activity[0]]  # ID
    for field in activity[1:]:
        normalized_field = normalize_text(field)
        normalized_activity.append(normalized_field)
    normalized_activities.append(normalized_activity)

# Create temporary tables for normalized data
cursor.execute(
    """
    CREATE TEMPORARY TABLE temp_activities (
        id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        supplies TEXT,
        instructions TEXT
    )
"""
)

cursor.executemany(
    """
    INSERT INTO temp_activities (id, title, description, supplies, instructions)
    VALUES (?, ?, ?, ?, ?)
""",
    normalized_activities,
)

# Compare fields using semantic similarity
similarity_threshold = 0.7
cursor.execute(
    """
    SELECT t1.id AS id1, t2.id AS id2,
           semantic_similarity(t1.title, t2.title) AS title_similarity,
           semantic_similarity(t1.description, t2.description) AS description_similarity,
           semantic_similarity(t1.supplies, t2.supplies) AS supplies_similarity,
           semantic_similarity(t1.instructions, t2.instructions) AS instructions_similarity
    FROM temp_activities t1
    JOIN temp_activities t2 ON t1.id < t2.id
    WHERE semantic_similarity(t1.title, t2.title) >= ?
       OR semantic_similarity(t1.description, t2.description) >= ?
       OR semantic_similarity(t1.supplies, t2.supplies) >= ?
       OR semantic_similarity(t1.instructions, t2.instructions) >= ?
""",
    (
        similarity_threshold,
        similarity_threshold,
        similarity_threshold,
        similarity_threshold,
    ),
)

# Fetch the potential duplicates
potential_duplicates = cursor.fetchall()

# Open a file for writing the output in the data/ directory
with open("data/potential_duplicates.txt", "w") as file:
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