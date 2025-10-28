import json

# Define all your database filenames in one place
USERS_FILE = 'users.json'
TRANSACTIONS_FILE = 'transactions.json'
SAVINGS_FILE = 'savings.json'
PEOPLE_FILE = 'people.json'

def read_data_file(filename, default_value):
    """
    Reads a JSON file.
    Returns default_value (e.g., [] or {}) if file not found or empty.
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            # Ensure data is of the expected type (list or dict)
            if not isinstance(data, type(default_value)):
                return default_value
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is invalid, return the default
        return default_value

def write_data_file(filename, data):
    """Writes data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)