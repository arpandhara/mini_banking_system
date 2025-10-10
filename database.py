import json

USERS_FILE = 'users.json'

def read_users():
    try:
        with open(USERS_FILE , 'r') as f:
            return json.load(f)
    except(FileNotFoundError , json.JSONDecodeError):
        return []
    
def write_users(users_data):
    with open(USERS_FILE , 'w') as f:
        json.dump(users_data , f , indent=4)