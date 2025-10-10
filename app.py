from flask import Flask , request , jsonify , session
from werkzeug.security import generate_password_hash , check_password_hash
import random

from database import read_users , write_users

app = Flask(__name__)
app.secret_key = '77ea0f9b96f802c9863be1af22696cb3'


# User login an sign up functionality

@app.route('/api/signup' , methods=['POST'])
def signUp():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    age = data.get('age')
    gender = data.get('gender')
    phoneNumber = data.get('phoneNumber')
    
    # check for is password entered or not 
    
    if not username or not password:
        return jsonify({'error' : 'Username and password are required'}) , 400
    
    if(int(age)<15 or int(age)>150):
        return jsonify({'error': 'age not valid'}) , 400
    
    if(len(phoneNumber)<10):
        return jsonify({'error': 'phone number must be of 10 numbers'}) , 400
    
    users = read_users()
    
    if not users:
        new_user_id = 1000
    else:
        max_id = max(user['user_id'] for user in users)
        new_user_id = max_id + 1;
        
        
        
    new_user = {
        "user_id" : new_user_id,
        "username" : username,
        "password_hash" : generate_password_hash(password),
        "balance" : 0.0,
        "age" : int(age),
        "gender" : gender,
        "phoneNumber" : int(phoneNumber)
    }
    
    users.append(new_user)
    write_users(users)
    
    return jsonify({
        "message" : f"User {username} created successfully",
        "user_id" : new_user_id
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
        return jsonify({"message": f"Welcome back, {username}!"}) , 200
    else:
        return jsonify({"error": "Invalid credentials provided"}), 401


if __name__ == '__main__':
    app.run(debug=True)