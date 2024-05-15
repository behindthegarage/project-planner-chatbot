import json

def chunk_emails(input_file, chunk_size):
    # Load the entire email data from the source JSON file
    with open(input_file, 'r') as file:
        emails = json.load(file)

    # Calculate the number of chunks
    total_emails = len(emails)
    num_chunks = (total_emails + chunk_size - 1) // chunk_size  # Ceiling division

    # Split the data into chunks and write each to a separate file
    for i in range(num_chunks):
        chunk = emails[i * chunk_size:(i + 1) * chunk_size]
        output_file = f'data/emails_chunk_{i+1}.json'
        with open(output_file, 'w') as file:
            json.dump(chunk, file, indent=4)
        print(f'Chunk {i+1} written to {output_file}')

# Example usage
chunk_emails('data/emails_cleaned.json', 10)