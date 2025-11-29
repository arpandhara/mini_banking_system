from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import string
import secrets
from database import users_collection
from utils import twilio_client, TWILIO_PHONE_NUMBER

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/signup', methods=['POST'])
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

@auth_bp.route('/api/login', methods=['POST'])
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


@auth_bp.route('/api/forgotPass', methods=['POST'])
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
 

@auth_bp.route('/api/change-password', methods=['POST'])
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

@auth_bp.route('/api/profile-data', methods=['GET'])
def get_profile_data():
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "User not logged in"}), 401
    
    user = users_collection.find_one({"user_id": user_id}, {'_id': 0, 'password_hash': 0})
    return jsonify(user), 200