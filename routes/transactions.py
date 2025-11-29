from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
import datetime
from database import users_collection, transactions_collection, savings_collection, people_collection
from utils import create_transaction_record

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/api/dashboard-data', methods=['GET'])
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

@transactions_bp.route('/api/process-payment', methods=['POST'])
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

@transactions_bp.route('/api/transactions-data', methods=['GET'])
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