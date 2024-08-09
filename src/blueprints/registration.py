from flask import Blueprint, request, jsonify, render_template, session, redirect
from src.models.registration import Registration, serialize_documents
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

registration_bp = Blueprint('registration', __name__)

# ---------------------------------------------------------------
# Helper function for encoding.

def json_encoder(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")

# ---------------------------------------------------------------

@registration_bp.route('/', methods=['GET'])
# @require_auth
def list_all_registrations():
   try:
      # Get the default page and page_size.
      page = int(request.args.get('page', 1))
      page_size = int(request.args.get('page_size', 100))

      # Calculate the number of documents to skip
      skip = (page - 1) * page_size
      
      # Setup the filters for the 'query' string.
      filter = {}
      if request.args.get('query'):
          filter['$or'] = [
            {'first_name': request.args.get('query')}, 
            {'last_name': request.args.get('query')},
            {'email': request.args.get('query')}  
          ]
      
      # If we have a 'kyc_status' then add it to the filter.
      if request.args.get('kyc_status'):
          filter['kyc_status'] = request.args.get('kyc_status')    

      sort = "-started_at"
      
      print('Query params', page_size, sort, skip, filter)
      
      # Query the db.
      documents = Registration.find(filter=filter, skip=skip, limit=page_size, sort=sort)
      
      document_list = [doc.model_dump(by_alias=True) for doc in documents]
      
      result = {
          'count': len(document_list),
          'data': document_list,
          'page': page,
          'page_size': page_size,
          'filter': filter,
          'skip': skip
      }
      
      return json.dumps(result, default=json_encoder), 200
   except Exception as e:
      print(e)
      return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------

@registration_bp.route('/<string:id>', methods=['GET'])
@require_auth
def get_all_registration(id):
    pre_reg = Registration.find_by_id(id)
    return json.dumps(pre_reg.dict(), default=str)  

# ---------------------------------------------------------------

@registration_bp.route('/<int:id>', methods=['PUT'])
def update_all_registration(id):
    return json.dumps({ 'msg': 'No Code set up for this route.'}, default=str)  

# ---------------------------------------------------------------

@registration_bp.route('/<string:id>', methods=['DELETE'])
@require_auth
def delete_all_registration(id):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(id):
            return jsonify({"error": "Invalid ObjectId"}), 400
        
        object_id = ObjectId(id)
        result = Registration.collection().delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Document not found"}), 404
        
        return jsonify({"message": "Document deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

