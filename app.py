# IMPORTED MODULES-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import secrets
import string
import time
import datetime
import os  # Added for environment variables
from flask import Flask , request , jsonify , session , send_from_directory
from werkzeug.security import generate_password_hash , check_password_hash 
from flask_cors import CORS
from dotenv import load_dotenv  # Added to load .env file
from twilio.rest import Client  # Added for Twilio
from twilio.base.exceptions import TwilioRestException  # Added for error handling

# Updated database imports
from database import (
    read_data_file, write_data_file,
    USERS_FILE, TRANSACTIONS_FILE, SAVINGS_FILE, PEOPLE_FILE
)

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app  , supports_credentials=True)
app.secret_key = '77ea0f9b96f802c9863be1af22696cb3' #SESSION KEY

# --- Twilio Configuration ---
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    print("WARNING: Twilio environment variables not set. SMS functionality will be disabled.")
# --- End Twilio Configuration ---


# --- HELPER FUNCTIONS ---

def find_user_by_id(user_id):
    """Finds a user in the users.json list by their ID (read-only)."""
    users = read_data_file(USERS_FILE, default_value=[])
    for user in users:
        if user.get('user_id') == user_id:
            return user
    return None

def find_user_and_index_by_id(users_list, user_id):
    """
    Finds a user and their index in a pre-loaded list.
    Returns (user_dict, index) or (None, -1).
    """
    for i, user in enumerate(users_list):
        if user.get('user_id') == user_id:
            return user, i
    return None, -1

def create_transaction_record(name, tx_type, amount, note=""):
    """Helper to create a standardized transaction dictionary."""
    return {
        "transaction_id": f"tid_{int(time.time() * 1000)}",
        "name": name,
        "type": tx_type,
        "amount": amount, # This can be positive or negative
        "date": datetime.datetime.now().strftime('%Y-%m-%d'),
        "description": note
    }


# User login an sign up functionality----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



@app.route('/api/signup' , methods=['POST'])
def signUp():
    data = request.get_json()
    fullName = data.get('username')
    password = data.get('password')
    age = data.get('age')
    gender = data.get('gender')
    phoneNumber = data.get('phoneNumber')
    
    # check for if password entered or not 
    
    if not fullName or not password or not age or not gender or not phoneNumber:
        return jsonify({'error': 'All fields are required'}), 400
    
    try:
        age_int = int(age)
        if age_int < 18 or age_int > 150:
            return jsonify({'error': 'Age must be between 18 and 150',
                            "signUp" :  False}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid age format' , 
                        "signUp" :  False}), 400

    if len(str(phoneNumber)) != 10:
        return jsonify({'error': 'Phone number must be exactly 10 digits' , 
                        "signUp" :  False}), 400
    
    # Use the new generic read function
    users = read_data_file(USERS_FILE, default_value=[])
    
    for user in users:
        if user.get('phoneNumber') == int(phoneNumber):
            return jsonify({'error': 'This phone number is already registered'}), 409
    
    if not users:
        new_user_id = 1000
    else:
        max_id = max(user['user_id'] for user in users)
        new_user_id = max_id + 1;
        
        
        
    new_user = {
        "user_id": new_user_id,
        "username": fullName,  # Storing fullName as username
        "password_hash": generate_password_hash(password),
        "balance": 0.0,
        "age": int(age),
        "gender": gender,
        "phoneNumber": int(phoneNumber)
    }
    
    users.append(new_user)
    # Use the new generic write function
    write_data_file(USERS_FILE, users)
    
    
    # --- NEW: INITIALIZE USER DATA IN OTHER FILES ---
    
    # Convert new_user_id to string for JSON keys
    user_id_str = str(new_user_id)
    
    try:
        # Initialize transactions (default is an object {})
        transactions_data = read_data_file(TRANSACTIONS_FILE, default_value={})
        transactions_data[user_id_str] = []
        write_data_file(TRANSACTIONS_FILE, transactions_data)
        
        # Initialize savings (default is an object {})
        savings_data = read_data_file(SAVINGS_FILE, default_value={})
        savings_data[user_id_str] = []
        write_data_file(SAVINGS_FILE, savings_data)
        
        # Initialize people (default is an object {})
        people_data = read_data_file(PEOPLE_FILE, default_value={})
        people_data[user_id_str] = []
        write_data_file(PEOPLE_FILE, people_data)

    except Exception as e:
        # This is a server-side error, but we should log it
        print(f"CRITICAL ERROR: Failed to initialize data files for user {user_id_str}: {e}")
        # We can still return success, as the user *was* created.
        pass
    
    # --- END OF NEW BLOCK ---
    
    session['user_id'] = new_user_id
    
    return jsonify({
        "message" : f"User {fullName} created successfully",
        "user_id" : new_user_id,
        "signUp" : True
    }),201


# login logic


@app.route('/api/login' , methods = ['POST'])
def login():
    data = request.get_json();
    username = data.get('username')
    password = data.get('password')
    
    try:
        user_id = int(data.get('user_id'))
    except(ValueError , TypeError):
        return jsonify({"error": "Valid User ID is required"}), 400
    
    if not username or not password or not user_id:
        return jsonify({'error' : 'Username, password and user_id are required'}) , 400
    
    # Use the new generic read function
    users = read_data_file(USERS_FILE, default_value=[])
    user_to_check = None
    
    for user in users:
        if(user['user_id'] == user_id):
            user_to_check = user
            break
        
    if(
        user_to_check 
       and user_to_check['username'] == username 
       and check_password_hash(user_to_check['password_hash'] , password)
       ):
        session['user_id'] = user_to_check['user_id']
        return jsonify({"message": f"Welcome back, {username}!",
                        "loggedIn" : True}) , 200
    else:
        return jsonify({"error": "Invalid credentials provided",
                        "loggedIn" : False}), 401
    
    
    
# forgot Password logic


@app.route('/api/forgotPass' , methods=['POST'])
def forgotPass():
    # pywhatkit and pyautogui imports are removed
    
    data = request.get_json()
    phoneNumber = data.get('phoneNumber')
    
    if not phoneNumber:
        return jsonify({'error' : 'Phone Number is required'}),400
    
    try:
        # FIX: Convert the incoming phone number string to an integer immediately.
        phoneNumber = int(phoneNumber)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid phone number format'}), 400
    
    # Use the new generic read function
    users = read_data_file(USERS_FILE, default_value=[])
    user_found = None
    user_index = -1
    
    for i, user in enumerate(users):
        if user.get('phoneNumber') == phoneNumber:
            user_found = user
            user_index = i
            break # Exit the loop once a user is found

    
    if not user_found:
        return jsonify({'error': 'Phone number not registered'}), 404
    
    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for i in range(6)) # 8-character random password
    temp_password = f'@0{temp_password}'
    users[user_index]['password_hash'] = generate_password_hash(temp_password)
    
    # Use the new generic write function
    write_data_file(USERS_FILE, users)
    
    # --- NEW: Twilio SMS Logic ---
    try:
        if not twilio_client or not TWILIO_PHONE_NUMBER:
            print("ERROR: Twilio client not configured.")
            raise Exception("Twilio client is not configured on the server.")

        # Format number for E.164 (assuming Indian numbers)
        phone_with_country_code = f"+91{phoneNumber}"
        message_body = f"Hello {user_found['username']},\n\nYour temporary password for Mini Bank is: {temp_password}\n\nPlease use this to log in and change your password immediately."

        # Send the SMS
        message = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_with_country_code
        )

        print(f"Twilio message sent: {message.sid}")
        
        return jsonify({
            "message": "A temporary password has been sent to your phone via SMS.",
            "isSMSSent": True  # Changed from isWhatsapp
        }), 200
        
    except TwilioRestException as e:
        print(f"Twilio REST Error: {e}")
        return jsonify({
            "error": f"Could not send SMS. Provider error: {e.msg}",
            "isSMSSent": False
        }), 500
    except Exception as e:
        print(f"General Error sending SMS: {e}")
        return jsonify({
            "error": "Server error: Could not send SMS. Check server configuration.",
            "isSMSSent": False
        }), 500
    # --- END: Twilio SMS Logic ---
 
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------



@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    # 1. Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    
    user_id_str = str(user_id)
    
    # 2. Get User's Core Info (Balance, Name)
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    user_balance = user.get('balance', 0.0)
    user_name = user.get('username', 'User')

    # 3. Read all data files
    transactions_data = read_data_file(TRANSACTIONS_FILE, default_value={})
    savings_data = read_data_file(SAVINGS_FILE, default_value={})
    people_data = read_data_file(PEOPLE_FILE, default_value={})

    # 4. Get this user's specific data
    # Use .get() for safety, defaulting to an empty list
    user_transactions = transactions_data.get(user_id_str, [])
    user_savings = savings_data.get(user_id_str, [])
    user_people = people_data.get(user_id_str, [])

    # 5. Calculate Monthly Income and Outcome
    total_income = 0.0
    total_outcome = 0.0
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year

    for tx in user_transactions:
        try:
            # Parse the date string into a datetime object
            tx_date = datetime.datetime.strptime(tx['date'], '%Y-%m-%d')
            
            # Check if the transaction is from the current month and year
            if tx_date.month == current_month and tx_date.year == current_year:
                if tx['amount'] > 0:
                    total_income += tx['amount']
                else:
                    total_outcome += tx['amount'] # This will be a negative sum
        except (ValueError, KeyError):
            # Skip transaction if date is missing or malformed
            print(f"Skipping transaction with bad date: {tx.get('transaction_id')}")
            pass
            
    # 6. Prepare data for frontend
    # Slicing with `[-4:]` gets the last 4 items (or fewer if the list is short)
    dashboard_payload = {
        "username": user_name,
        "total_balance": user_balance,
        "monthly_income": total_income,
        "monthly_outcome": total_outcome,
        "all_transactions": user_transactions, # Send all, frontend can display them
        "last_4_savings": user_savings[-4:],
        "last_4_people": user_people[-4:],
        "userAccountNumber" : user_id_str
    }

    return jsonify(dashboard_payload), 200

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------



# --- SAVINGS ROUTES ---

@app.route('/api/savings', methods=['GET'])
def get_savings():
    """Fetches all savings goals for the logged-in user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    
    user_id_str = str(user_id)
    savings_data = read_data_file(SAVINGS_FILE, default_value={})
    user_savings = savings_data.get(user_id_str, [])
    
    # Return newest first
    return jsonify(user_savings[::-1]), 200

@app.route('/api/savings', methods=['POST'])
def add_saving():
    """Adds a new savings goal for the logged-in user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    
    data = request.get_json()
    user_id_str = str(user_id)
    
    item_name = data.get('itemName')
    target_amount_str = data.get('targetAmount')
    color_code = data.get('colorCode')
    description = data.get('description')
    
    if not item_name or not target_amount_str:
        return jsonify({"error": "Item name and target amount are required"}), 400
    
    try:
        target_amount = float(target_amount_str)
        if target_amount <= 0:
            raise ValueError("Target amount must be positive")
    except (ValueError, TypeError):
        return jsonify({"error": "Target amount must be a positive number"}), 400
    
    # Generate unique saving ID (prefix 'sid_' + timestamp in milliseconds)
    saving_id = f"sid_{int(time.time() * 1000)}"
    
    new_saving = {
        "saving_id": saving_id,
        "name": item_name,
        "target_amount": target_amount,
        "saved_amount": 0.0,  # New savings always start at 0
        "color_code": color_code,
        "description": description,
        "created_at": datetime.datetime.now().strftime('%Y-%m-%d')
    }
    
    # Read, update, and write
    savings_data = read_data_file(SAVINGS_FILE, default_value={})
    user_savings = savings_data.get(user_id_str, [])
    user_savings.append(new_saving)
    savings_data[user_id_str] = user_savings
    write_data_file(SAVINGS_FILE, savings_data)
    
    # Return the newly created object
    return jsonify(new_saving), 201


@app.route('/api/savingsDelete' , methods = ['POST'])
def delete_savings():
    "delete a savings for the logged in user"
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    
    data = request.get_json()
    user_id_str = str(user_id)
    
    
    savingsId_short = data.get('savingsId')
    
    if not savingsId_short:
        return jsonify({"error": "Saving ID is required"}), 400
    
    target_saving_id = f"sid_{savingsId_short}"
    
    savings_data = read_data_file(SAVINGS_FILE, default_value={})
    user_savings = savings_data.get(user_id_str, [])
    
    updated_user_savings = [
        saving for saving in user_savings
        if saving.get("saving_id") != target_saving_id
    ]
    
    if len(updated_user_savings) < len(user_savings):
        savings_data[user_id_str] = updated_user_savings
        write_data_file(SAVINGS_FILE,savings_data)
        
        return jsonify({"message": f"Saving {target_saving_id} deleted successfully"}), 200
    else:
        # The loop finished, but no matching ID was found
        return jsonify({"error": "Saving not found"}), 404

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --- NEW: PAYMENT PROCESSING ROUTE ---
@app.route('/api/process-payment', methods=['POST'])
def process_payment():
    
    # 1. --- AUTHENTICATION ---
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    
    user_id_str = str(user_id)
    data = request.get_json()

    # 2. --- GET COMMON DATA ---
    password = data.get('password')
    amount_str = data.get('amount')
    transaction_type = data.get('transaction_type')
    note = data.get('note', "")

    if not password or not amount_str or not transaction_type:
        return jsonify({"error": "Password, amount, and transaction type are required"}), 400

    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({"error": "Amount must be a positive number"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    # 3. --- LOAD DATA & VALIDATE SENDER ---
    users = read_data_file(USERS_FILE, default_value=[])
    transactions_data = read_data_file(TRANSACTIONS_FILE, default_value={})
    
    sender, sender_index = find_user_and_index_by_id(users, user_id)
    
    if not sender:
        return jsonify({"error": "Sender account not found"}), 404 # Should not happen if logged in
        
    if not check_password_hash(sender['password_hash'], password):
        return jsonify({"error": "Invalid password"}), 403

    # 4. --- TRANSACTION-SPECIFIC LOGIC ---
    
    # --- DEPOSIT ---
    if transaction_type == 'deposit':
        sender['balance'] += amount
        tx_name = "Deposit"
        tx_type = "Deposit"
        tx_amount = amount
        
        new_tx = create_transaction_record(tx_name, tx_type, tx_amount, note)
        user_tx = transactions_data.get(user_id_str, [])
        user_tx.append(new_tx)
        transactions_data[user_id_str] = user_tx
        
    # --- WITHDRAW ---
    elif transaction_type == 'withdraw':
        if sender['balance'] < amount:
            return jsonify({"error": "Insufficient funds"}), 400
            
        sender['balance'] -= amount
        tx_name = "Withdrawal"
        tx_type = "Withdrawal"
        tx_amount = -amount # Store as negative
        
        new_tx = create_transaction_record(tx_name, tx_type, tx_amount, note)
        user_tx = transactions_data.get(user_id_str, [])
        user_tx.append(new_tx)
        transactions_data[user_id_str] = user_tx

    # --- BANK TRANSFER (PAY STRANGER / FRIEND) ---
    elif transaction_type == 'bank_transfer':
        recipient_account_str = data.get('recipient_account')
        if not recipient_account_str:
            return jsonify({"error": "Recipient account number is required"}), 400
            
        try:
            recipient_id = int(recipient_account_str)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid recipient account number"}), 400
            
        if recipient_id == user_id:
            return jsonify({"error": "You cannot send money to yourself"}), 400
            
        if sender['balance'] < amount:
            return jsonify({"error": "Insufficient funds"}), 400
            
        recipient, recipient_index = find_user_and_index_by_id(users, recipient_id)
        
        if not recipient:
            return jsonify({"error": "Recipient account not found"}), 404
            
        # Perform transfer
        sender['balance'] -= amount
        recipient['balance'] += amount
        
        # Update users list
        users[sender_index] = sender
        users[recipient_index] = recipient
        
        # Create transaction for SENDER
        sender_tx = create_transaction_record(
            name=f"Transfer to {recipient['username']}",
            tx_type="Bank Transfer",
            amount=-amount,
            # recipient_id = recipient_account_str,
            note=note
        )
        sender_tx_list = transactions_data.get(user_id_str, [])
        sender_tx_list.append(sender_tx)
        transactions_data[user_id_str] = sender_tx_list
        
        # Create transaction for RECIPIENT
        recipient_tx = create_transaction_record(
            name=f"Transfer from {sender['username']}",
            tx_type="Bank Transfer",
            amount=amount,
            note=note
        )
        recipient_tx_list = transactions_data.get(str(recipient_id), [])
        recipient_tx_list.append(recipient_tx)
        transactions_data[str(recipient_id)] = recipient_tx_list

    # --- SAVING DEPOSIT ---
    elif transaction_type == 'saving_deposit':
        saving_id = data.get('saving_id')
        if not saving_id:
            return jsonify({"error": "Saving Goal ID is required"}), 400
            
        if sender['balance'] < amount:
            return jsonify({"error": "Insufficient funds"}), 400
            
        # Load, modify, and save savings data
        savings_data = read_data_file(SAVINGS_FILE, default_value={})
        user_savings = savings_data.get(user_id_str, [])
        
        saving_found = False
        tx_name = "Saving Deposit" # Default name
        for saving in user_savings:
            if saving.get('saving_id') == saving_id:
                saving['saved_amount'] += amount
                tx_name = f"Deposit to {saving['name']}"
                saving_found = True
                break
                
        if not saving_found:
            return jsonify({"error": "Saving goal not found"}), 404
            
        # Update sender's balance
        sender['balance'] -= amount
        
        # Create transaction record
        new_tx = create_transaction_record(
            name=tx_name,
            tx_type="Saving Deposit",
            amount=-amount,
            note=note
        )
        user_tx = transactions_data.get(user_id_str, [])
        user_tx.append(new_tx)
        transactions_data[user_id_str] = user_tx
        
        # Write updated savings data
        savings_data[user_id_str] = user_savings
        write_data_file(SAVINGS_FILE, savings_data)
    
    else:
        return jsonify({"error": "Invalid transaction type"}), 400

    # 5. --- SAVE ALL CHANGES & RESPOND ---
    users[sender_index] = sender # Ensure sender's updates are in the list
    write_data_file(USERS_FILE, users)
    write_data_file(TRANSACTIONS_FILE, transactions_data)

    return jsonify({
        "message": "Transaction successful!",
        "new_balance": sender['balance']
    }), 200


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/api/profile-data', methods=['GET'])
def get_profile_data():
    """
    Fetches basic profile information for the logged-in user.
    """
    # 1. Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    
    # 2. Get User's Core Info
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # 3. Prepare payload with all necessary details
    profile_payload = {
        "username": user.get('username', 'User'),
        "user_id": user.get('user_id', 'N/A'),
        "phoneNumber": user.get('phoneNumber', 'N/A'),
        "age": user.get('age', 'N/A'),
        "gender": user.get('gender', 'N/A')
    }
    
    return jsonify(profile_payload), 200


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --- NEW: CHANGE PASSWORD ROUTE ---
@app.route('/api/change-password', methods=['POST'])
def change_password():
    """
    Allows a logged-in user to change their password.
    """
    # 1. Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    # 2. Get data from request
    data = request.get_json()
    old_password = data.get('oldPassword')
    new_password = data.get('newPassword')
    confirm_new_password = data.get('confirmNewPassword')

    # 3. Validate input
    if not old_password or not new_password or not confirm_new_password:
        return jsonify({"error": "All password fields are required"}), 400

    if new_password != confirm_new_password:
        return jsonify({"error": "New passwords do not match"}), 400

    # 4. Find the user
    users = read_data_file(USERS_FILE, default_value=[])
    user, user_index = find_user_and_index_by_id(users, user_id)

    if not user:
        session.clear() # Clear bad session
        return jsonify({"error": "User account not found"}), 404

    # 5. Verify old password
    if not check_password_hash(user['password_hash'], old_password):
        return jsonify({"error": "Incorrect old password"}), 403

    # 6. Hash and save new password
    new_password_hash = generate_password_hash(new_password)
    user['password_hash'] = new_password_hash
    users[user_index] = user
    
    write_data_file(USERS_FILE, users)

    # 7. Return success
    return jsonify({"message": "Password updated successfully"}), 200


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
    app.run(debug=True)