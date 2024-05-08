import json

def save_to_json(data, file_path):
    """Save data to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def load_from_json(file_path):
    """Load data from a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)