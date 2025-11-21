import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the URI from .env
MONGO_URI = os.environ.get('MONGO_URI')

if not MONGO_URI:
    raise ValueError("No MONGO_URI found in environment variables")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client['MiniBankingSystem']

# Define Collections
users_collection = db['users']
transactions_collection = db['transactions']
savings_collection = db['savings']
people_collection = db['people']

# Helper to checking connection
def check_db_connection():
    try:
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas successfully!")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")

check_db_connection()