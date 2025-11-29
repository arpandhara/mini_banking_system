import os
import time
import datetime
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# --- Twilio Configuration ---
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def create_transaction_record(user_id, name, tx_type, amount, note="", status="Completed"):
    """Creates a transaction object compatible with MongoDB"""
    return {
        "user_id": user_id,  # Link to the user
        "transaction_id": f"tid_{int(time.time() * 1000)}",
        "name": name,
        "type": tx_type,
        "amount": amount,
        "date": datetime.datetime.now().strftime('%Y-%m-%d'),
        "description": note,
        "status": status
    }