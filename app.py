# IMPORTED MODULES-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


from flask import Flask , request , jsonify , session
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
    
    
    
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
    app.run(debug=True)