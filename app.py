# IMPORTED MODULES------------------------------------------------------------
import secrets
import string
import time
import datetime
import os
from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# NEW DATABASE IMPORTS
from database import (
    users_collection, 
    transactions_collection, 
    savings_collection, 
    people_collection
)

# ----------------------------------------------------------------------------

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = '77ea0f9b96f802c9863be1af22696cb3'

# --- Twilio Configuration ---
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# --- HELPER FUNCTIONS ---

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

# --- ROUTES ---

@app.route('/api/signup', methods=['POST'])
def signUp():
    data = request.get_json()
    fullName = data.get('username')
    password = data.get('password')
    age = data.get('age')
    gender = data.get('gender')
    phoneNumber = data.get('phoneNumber')
    
    if not fullName or not password or not age or not gender or not phoneNumber:
        return jsonify({'error': 'All fields are required'}), 400
    
    try:
        age_int = int(age)
        if age_int < 18 or age_int > 150:
            return jsonify({'error': 'Age must be between 18 and 150', "signUp": False}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid age format', "signUp": False}), 400

    if len(str(phoneNumber)) != 10:
        return jsonify({'error': 'Phone number must be 10 digits', "signUp": False}), 400
    
    # Check if phone number exists in MongoDB
    if users_collection.find_one({"phoneNumber": int(phoneNumber)}):
        return jsonify({'error': 'Phone number already registered'}), 409
    
    # Generate new User ID
    last_user = users_collection.find_one(sort=[("user_id", -1)])
    new_user_id = 1000 if not last_user else last_user['user_id'] + 1
        
    new_user = {
        "user_id": new_user_id,
        "username": fullName,
        "password_hash": generate_password_hash(password),
        "balance": 0.0,
        "age": int(age),
        "gender": gender,
        "phoneNumber": int(phoneNumber)
    }
    
    # Insert into MongoDB
    users_collection.insert_one(new_user)
    
    # Note: We don't need to initialize empty lists for transactions/savings in Mongo.
    # They are created when data is inserted.
    
    session['user_id'] = new_user_id
    
    return jsonify({
        "message": f"User {fullName} created successfully",
        "user_id": new_user_id,
        "signUp": True
    }), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    try:
        user_id = int(data.get('user_id'))
    except (ValueError, TypeError):
        return jsonify({"error": "Valid User ID is required"}), 400
    
    # Find user in MongoDB
    user = users_collection.find_one({"user_id": user_id})
        
    if (user and user['username'] == username and 
        check_password_hash(user['password_hash'], password)):
        session['user_id'] = user['user_id']
        return jsonify({"message": f"Welcome back, {username}!", "loggedIn": True}), 200
    else:
        return jsonify({"error": "Invalid credentials", "loggedIn": False}), 401


@app.route('/api/forgotPass', methods=['POST'])
def forgotPass():
    data = request.get_json()
    phoneNumber = data.get('phoneNumber')
    
    try:
        phoneNumber = int(phoneNumber)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid phone number'}), 400
    
    # Find user
    user = users_collection.find_one({"phoneNumber": phoneNumber})
    
    if not user:
        return jsonify({'error': 'Phone number not registered'}), 404
    
    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for i in range(6))
    temp_password_fmt = f'@0{temp_password}'
    
    # Update password in MongoDB
    users_collection.update_one(
        {"user_id": user['user_id']},
        {"$set": {"password_hash": generate_password_hash(temp_password_fmt)}}
    )
    
    # Twilio SMS Logic
    try:
        if twilio_client:
            message_body = f"Hello {user['username']},\n\nYour temporary password is: {temp_password_fmt}"
            twilio_client.messages.create(
                body=message_body,
                from_=TWILIO_PHONE_NUMBER,
                to=f"+91{phoneNumber}"
            )
            return jsonify({"message": "Temporary password sent via SMS.", "isSMSSent": True}), 200
    except Exception as e:
        print(f"SMS Error: {e}")
        # Return success anyway so user knows password changed, but warn about SMS
        return jsonify({"message": "Password changed, but SMS failed.", "isSMSSent": False, "temp_pass": temp_password_fmt}), 200

    return jsonify({"error": "SMS service unavailable", "isSMSSent": False}), 500


@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    # Fetch related data from MongoDB collections
    # Exclude _id field from results using projection {'_id': 0}
    user_transactions = list(transactions_collection.find({"user_id": user_id}, {'_id': 0}))
    user_savings = list(savings_collection.find({"user_id": user_id}, {'_id': 0}))
    user_people = list(people_collection.find({"user_id": user_id}, {'_id': 0}))

    total_income = 0.0
    total_outcome = 0.0
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year

    for tx in user_transactions:
        try:
            tx_date = datetime.datetime.strptime(tx['date'], '%Y-%m-%d')
            if tx_date.month == current_month and tx_date.year == current_year:
                if tx['amount'] > 0:
                    total_income += tx['amount']
                else:
                    total_outcome += tx['amount']
        except:
            pass
            
    dashboard_payload = {
        "username": user.get('username'),
        "total_balance": user.get('balance', 0.0),
        "monthly_income": total_income,
        "monthly_outcome": total_outcome,
        "all_transactions": user_transactions,
        "last_4_savings": user_savings[-4:],
        "last_4_people": user_people[-4:],
        "userAccountNumber": str(user_id)
    }
    return jsonify(dashboard_payload), 200


@app.route('/api/savings', methods=['GET', 'POST'])
def handle_savings():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    if request.method == 'GET':
        savings = list(savings_collection.find({"user_id": user_id}, {'_id': 0}))
        return jsonify(savings[::-1]), 200

    if request.method == 'POST':
        data = request.get_json()
        try:
            target_amount = float(data.get('targetAmount'))
            if target_amount <= 0: raise ValueError()
        except:
            return jsonify({"error": "Invalid target amount"}), 400

        new_saving = {
            "user_id": user_id,
            "saving_id": f"sid_{int(time.time() * 1000)}",
            "name": data.get('itemName'),
            "target_amount": target_amount,
            "saved_amount": 0.0,
            "color_code": data.get('colorCode'),
            "description": data.get('description'),
            "created_at": datetime.datetime.now().strftime('%Y-%m-%d')
        }
        
        savings_collection.insert_one(new_saving)
        
        # Return object without _id for frontend
        new_saving.pop('_id')
        return jsonify(new_saving), 201


@app.route('/api/savingsDelete', methods=['POST'])
def delete_savings():
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "User not logged in"}), 401
    
    data = request.get_json()
    saving_id = f"sid_{data.get('savingsId')}"
    
    # Find the saving
    saving = savings_collection.find_one({"user_id": user_id, "saving_id": saving_id})
    
    if saving:
        amount = saving.get('saved_amount', 0.0)
        if amount > 0:
            # Refund user
            users_collection.update_one(
                {"user_id": user_id}, 
                {"$inc": {"balance": amount}}
            )
            # Log Transaction
            refund_tx = create_transaction_record(
                user_id, 
                f"Refund from '{saving.get('name')}'", 
                "Refund", 
                amount, 
                "Saving goal deleted."
            )
            transactions_collection.insert_one(refund_tx)
        
        # Delete saving
        savings_collection.delete_one({"_id": saving['_id']})
        return jsonify({"message": f"Deleted. Refunded: {amount}"}), 200
        
    return jsonify({"error": "Saving not found"}), 404


@app.route('/api/process-payment', methods=['POST'])
def process_payment():
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "User not logged in"}), 401
    
    data = request.get_json()
    password = data.get('password')
    try:
        amount = float(data.get('amount'))
    except (ValueError, TypeError):
         return jsonify({"error": "Invalid amount"}), 400

    tx_type = data.get('transaction_type')
    note = data.get('note', "")
    
    sender = users_collection.find_one({"user_id": user_id})
    
    if not check_password_hash(sender['password_hash'], password):
        return jsonify({"error": "Invalid password"}), 403

    # --- HANDLE TRANSACTIONS ---
    if tx_type == 'deposit':
        users_collection.update_one({"user_id": user_id}, {"$inc": {"balance": amount}})
        tx = create_transaction_record(user_id, "Deposit", "Deposit", amount, note)
        transactions_collection.insert_one(tx)

    elif tx_type == 'withdraw':
        if sender['balance'] < amount: return jsonify({"error": "Insufficient funds"}), 400
        users_collection.update_one({"user_id": user_id}, {"$inc": {"balance": -amount}})
        tx = create_transaction_record(user_id, "Withdrawal", "Withdrawal", -amount, note)
        transactions_collection.insert_one(tx)

    elif tx_type == 'bank_transfer':
        recipient_id = int(data.get('recipient_account'))
        if recipient_id == user_id: return jsonify({"error": "Cannot self-transfer"}), 400
        if sender['balance'] < amount: return jsonify({"error": "Insufficient funds"}), 400
        
        recipient = users_collection.find_one({"user_id": recipient_id})
        if not recipient: return jsonify({"error": "Recipient not found"}), 404
        
        # Update Balances
        users_collection.update_one({"user_id": user_id}, {"$inc": {"balance": -amount}})
        users_collection.update_one({"user_id": recipient_id}, {"$inc": {"balance": amount}})
        
        # Log for Sender
        tx_sender = create_transaction_record(user_id, f"Transfer to {recipient['username']}", "Bank Transfer", -amount, note)
        transactions_collection.insert_one(tx_sender)
        
        # Log for Recipient
        tx_recipient = create_transaction_record(recipient_id, f"Transfer from {sender['username']}", "Bank Transfer", amount, note)
        transactions_collection.insert_one(tx_recipient)

    elif tx_type == 'saving_deposit':
        saving_id = data.get('saving_id')
        if sender['balance'] < amount: return jsonify({"error": "Insufficient funds"}), 400
        
        saving = savings_collection.find_one({"user_id": user_id, "saving_id": saving_id})
        if not saving: return jsonify({"error": "Saving goal not found"}), 404
        
        # Update Balances
        users_collection.update_one({"user_id": user_id}, {"$inc": {"balance": -amount}})
        savings_collection.update_one({"_id": saving['_id']}, {"$inc": {"saved_amount": amount}})
        
        tx = create_transaction_record(user_id, f"Deposit to {saving['name']}", "Saving Deposit", -amount, note)
        transactions_collection.insert_one(tx)
    
    else:
        return jsonify({"error": "Invalid transaction type"}), 400

    # --- CRITICAL FIX: Fetch the updated balance to return to frontend ---
    updated_sender = users_collection.find_one({"user_id": user_id})
    new_balance = updated_sender['balance']

    return jsonify({
        "message": "Transaction successful!",
        "new_balance": new_balance  # <-- This was missing!
    }), 200

@app.route('/api/profile-data', methods=['GET'])
def get_profile_data():
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "User not logged in"}), 401
    
    user = users_collection.find_one({"user_id": user_id}, {'_id': 0, 'password_hash': 0})
    return jsonify(user), 200


@app.route('/api/change-password', methods=['POST'])
def change_password():
    user_id = session.get('user_id')
    data = request.get_json()
    
    if data['newPassword'] != data['confirmNewPassword']:
        return jsonify({"error": "Passwords do not match"}), 400
        
    user = users_collection.find_one({"user_id": user_id})
    if not check_password_hash(user['password_hash'], data['oldPassword']):
        return jsonify({"error": "Incorrect old password"}), 403
        
    users_collection.update_one(
        {"user_id": user_id}, 
        {"$set": {"password_hash": generate_password_hash(data['newPassword'])}}
    )
    return jsonify({"message": "Password updated"}), 200


@app.route('/api/transactions-data', methods=['GET'])
def get_transactions_page():
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "User not logged in"}), 401
    
    user = users_collection.find_one({"user_id": user_id})
    txs = list(transactions_collection.find({"user_id": user_id}, {'_id': 0}))
    savings = list(savings_collection.find({"user_id": user_id}))
    
    total_savings = sum(s.get('saved_amount', 0) for s in savings)
    total_income = sum(t['amount'] for t in txs if t['amount'] > 0)
    total_outcome = sum(t['amount'] for t in txs if t['amount'] < 0)
    
    return jsonify({
        "username": user['username'],
        "total_balance": user['balance'],
        "total_savings": total_savings,
        "total_income": total_income,
        "total_outcome": total_outcome,
        "transactions": txs
    }), 200


@app.route('/api/people', methods=['GET', 'POST'])
def handle_people():
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "User not logged in"}), 401

    if request.method == 'GET':
        people = list(people_collection.find({"user_id": user_id}, {'_id': 0}))
        for p in people:
            p['full_account_number'] = f"3594 1899 3455 {p['account_id']}"
        return jsonify(people[::-1]), 200

    if request.method == 'POST':
        data = request.get_json()
        contact_acc = int(data.get('contactAccount'))
        
        if contact_acc == user_id: return jsonify({"error": "Cannot add self"}), 400
        
        # Verify contact exists in bank
        contact_user = users_collection.find_one({"user_id": contact_acc})
        if not contact_user: return jsonify({"error": "Account not found"}), 404
        
        # Check dupes
        if people_collection.find_one({"user_id": user_id, "account_id": contact_acc}):
            return jsonify({"error": "Contact already exists"}), 409
            
        new_person = {
            "user_id": user_id,
            "people_id": f"pid_{int(time.time() * 1000)}",
            "name": data.get('contactName'),
            "phone": str(contact_user.get('phoneNumber')),
            "account_id": contact_acc,
            "relation": data.get('contactRelation')
        }
        people_collection.insert_one(new_person)
        new_person.pop('_id')
        new_person['full_account_number'] = f"3594 1899 3455 {contact_acc}"
        return jsonify(new_person), 201


@app.route('/api/people/<string:people_id>', methods=['DELETE', 'PUT'])
def manage_person(people_id):
    user_id = session.get('user_id')
    if request.method == 'DELETE':
        res = people_collection.delete_one({"user_id": user_id, "people_id": people_id})
        if res.deleted_count: return jsonify({"message": "Deleted"}), 200
        return jsonify({"error": "Not found"}), 404

    if request.method == 'PUT':
        data = request.get_json()
        res = people_collection.find_one_and_update(
            {"user_id": user_id, "people_id": people_id},
            {"$set": {
                "name": data.get('contactName'),
                "relation": data.get('contactRelation')
            }},
            return_document=True
        )
        if res:
            res.pop('_id')
            return jsonify(res), 200
        return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)