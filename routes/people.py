from flask import Blueprint, request, jsonify, session
import time
from database import users_collection, people_collection

people_bp = Blueprint('people', __name__)

@people_bp.route('/api/people', methods=['GET', 'POST'])
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

@people_bp.route('/api/people/<string:people_id>', methods=['DELETE', 'PUT'])
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