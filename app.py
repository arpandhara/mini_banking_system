# IMPORTED MODULES-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import secrets
import string
import time
import datetime
from flask import Flask , request , jsonify , session , send_from_directory
from werkzeug.security import generate_password_hash , check_password_hash 
from flask_cors import CORS
# Updated database imports
from database import (
    read_data_file, write_data_file,
    USERS_FILE, TRANSACTIONS_FILE, SAVINGS_FILE, PEOPLE_FILE
)



# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



app = Flask(__name__)
CORS(app  , supports_credentials=True)
app.secret_key = '77ea0f9b96f802c9863be1af22696cb3' #SESSION KEY

# --- HELPER FUNCTION ---
def find_user_by_id(user_id):
    """Finds a user in the users.json list by their ID."""
    users = read_data_file(USERS_FILE, default_value=[])
    for user in users:
        if user.get('user_id') == user_id:
            return user
    return None
# -----------------------


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
    import pywhatkit
    import pyautogui
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
    
    try:
        phone_with_country_code = f"+91{phoneNumber}"
        message = f"Hello {user_found['username']},\n\nYour temporary password for Mini Bank is: {temp_password}\n\nPlease use this to log in and change your password immediately."

        pywhatkit.sendwhatmsg_instantly(
            phone_with_country_code,
            message,
            wait_time=250,        # Increased from 15 to 25 seconds
            tab_close=True,
            close_time=5         # Wait 5 seconds before closing the tab
        )

        return jsonify({
            "message": "A temporary password has been sent to your WhatsApp.",
            "isWhatsapp": True
        }), 200
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return jsonify({
            "error": "Could not send password via WhatsApp. Please ensure you have WhatsApp linked.",
            "isWhatsapp": False
        }), 500


 
    
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




if __name__ == '__main__':
    app.run(debug=True)
