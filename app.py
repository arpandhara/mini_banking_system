# IMPORTED MODULES-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import secrets
import string
import time
from flask import Flask , request , jsonify , session , send_from_directory
from werkzeug.security import generate_password_hash , check_password_hash 
from flask_cors import CORS
from database import read_users , write_users



# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



app = Flask(__name__)
CORS(app)
app.secret_key = '77ea0f9b96f802c9863be1af22696cb3' #SESSION KEY




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
    
    users = read_users()
    
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
    write_users(users)
    
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
    
    users = read_users()
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
    
    users = read_users()
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
    write_users(users)
    
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


if __name__ == '__main__':
    app.run(debug=True)