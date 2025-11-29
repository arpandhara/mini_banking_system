import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Import Blueprints
from routes.auth import auth_bp
from routes.transactions import transactions_bp
from routes.savings import savings_bp
from routes.people import people_bp

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = '77ea0f9b96f802c9863be1af22696cb3'

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(savings_bp)
app.register_blueprint(people_bp)

if __name__ == '__main__':
    app.run(debug=True)