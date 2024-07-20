from flask import Blueprint, request, jsonify, render_template, session, redirect
from src.models.pre_registration import PreRegistration, serialize_documents
import json
from bson.objectid import ObjectId
from datetime import datetime
from functools import wraps

# ---------------------------------------------------------------
# Auth function to enforce a route.
def require_auth(f):
   @wraps(f)
   def decorated_function(*args, **kwargs):
      user = session.get('user')
      if not user:
         return redirect('/login')
      return f(*args, **kwargs)
   return decorated_function

pre_registration_bp = Blueprint('pre_registration', __name__)

# In-memory "database" for the sake of this example
pre_registrations = []

# ---------------------------------------------------------------
# Helper function for encoding.

def json_encoder(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")

# ---------------------------------------------------------------

@pre_registration_bp.route('/', methods=['GET'])
@require_auth
def list_pre_registrations():
   try:
      documents = PreRegistration.find()
      document_list = [doc.model_dump(by_alias=True) for doc in documents]
      return json.dumps(document_list, default=json_encoder), 200
   except Exception as e:
      print(e)
      return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------
@pre_registration_bp.route('', methods=['POST'])
def create_pre_registration():
   try:
      data = request.get_json()
      if not data:
        return jsonify({'msg': 'No data provided'}), 400

      if not data:
        return jsonify({'msg': 'No data provided'}), 400
            
      pre_reg = PreRegistration(**data)
      pre_reg.save()
    
      return jsonify({ 
        'msg': 'New Pre-Registration Created', 
        'data': pre_reg.safe_serialize() 
      }), 200

   except Exception as e:
      return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------
@pre_registration_bp.route('/<string:id>', methods=['GET'])
@require_auth
def get_pre_registration(id):
    pre_reg = PreRegistration.find_by_id(id)
    return json.dumps(pre_reg.dict(), default=str)  

@pre_registration_bp.route('/<int:id>', methods=['PUT'])
def update_pre_registration(id):
    return json.dumps({ 'msg': 'No Code set up for this route.'}, default=str)  

# ---------------------------------------------------------------

@pre_registration_bp.route('/<string:id>', methods=['DELETE'])
@require_auth
def delete_pre_registration(id):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(id):
            return jsonify({"error": "Invalid ObjectId"}), 400
        
        object_id = ObjectId(id)
        result = PreRegistration.collection().delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Document not found"}), 404
        
        return jsonify({"message": "Document deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------
# This is a process that will take the Pre-Registration and 
# feed it into the KYC process.

@pre_registration_bp.route('/<string:id>/kyc_start', methods=['POST'])
@require_auth
def pre_registration_to_kyc(id):
    try:
        # Validate ObjectId.
        if not ObjectId.is_valid(id):
            return jsonify({ "error": "Invalid ObjectId" }), 400

        result = PreRegistration.find_by_id(id)
        
        # If no result then return a error message.
        if result is None:
            return jsonify({ "error": "No Pre-registration record found."}), 404
        
        # Code to send the data to the KYC pre-registration process.
        return jsonify({"message": "Start the KYC."}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
