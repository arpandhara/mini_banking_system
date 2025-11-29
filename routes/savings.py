from flask import Blueprint, request, jsonify, session
import time
import datetime
from database import users_collection, savings_collection, transactions_collection
from utils import create_transaction_record

savings_bp = Blueprint('savings', __name__)

@savings_bp.route('/api/savings', methods=['GET', 'POST'])
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

@savings_bp.route('/api/savingsDelete', methods=['POST'])
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