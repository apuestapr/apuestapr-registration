from flask import Blueprint, request, jsonify, render_template, abort, session, redirect
from src.models.registration import Registration
from src.shufti import run_verification_request, handle_callback
from src.onfido import run_verification_request as onfido_run_verification_request, update_check_status, generate_sdk_token, run_check
from src.onfido import run_verification_request_new as onfido_run_verification_request_new
from src.whitehat import create_account, get_player_id

import json
from bson.objectid import ObjectId
# from datetime import datetime
from functools import wraps
from src.models.registration import Registration
import datetime

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
      documents = Registration.find(sort="-started_at")
      document_list = [doc.model_dump(by_alias=True) for doc in documents]
      return json.dumps(document_list, default=json_encoder), 200
   except Exception as e:
      print(e)
      return jsonify({"error": str(e)}), 500

# # ---------------------------------------------------------------
# @registration_bp.route('/create', methods=['POST'])
# def create_all_registration():
#    try:
#       data = request.get_json()
#       if not data:
#         return jsonify({'msg': 'No data provided'}), 400

#       if not data:
#         return jsonify({'msg': 'No data provided'}), 400
            
#       registration = Registration(**data)
#       registration.save()
    
#       return jsonify({ 
#         'msg': 'New Registration Created', 
#         'data': registration.safe_serialize() 
#       }), 200

#    except Exception as e:
#       return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------
@pre_registration_bp.route('/create', methods=['POST'])
def create_pre_registration():
   try:
      data = request.get_json()
      if not data:
        return jsonify({'msg': 'No data provided'}), 400

      if not data:
        return jsonify({'msg': 'No data provided'}), 400
            
      print(data)
      
      pre_reg = Registration(**data)
      pre_reg.started_at = datetime.datetime.utcnow()
      
      pre_reg.save()
    
      return jsonify({ 
        'msg': 'New Pre-Registration Created', 
        'data': pre_reg.safe_serialize() 
      }), 200

   except Exception as e:
      print(e)
      return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------
@pre_registration_bp.route('/get/<string:id>', methods=['GET'])
@require_auth
def get_pre_registration(id):
    pre_reg = Registration.find_by_id(id)
    return json.dumps(pre_reg.dict(), default=str)  

@pre_registration_bp.route('/<int:id>', methods=['PUT'])
def update_pre_registration(id):
    return json.dumps({ 'msg': 'No Code set up for this route.'}, default=str)  

# ---------------------------------------------------------------

@pre_registration_bp.route('/delete/<string:id>', methods=['DELETE'])
@require_auth
def delete_pre_registration(id):
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

# ---------------------------------------------------------------
# This is the route for the registration form that a 
# public (non-authenticated) user will need to get started.

@pre_registration_bp.route('/start')
def start_pre_registration():
   return render_template('registration-start.html')

# ---------------------------------------------------------------
# This endpoint is public and allows for access to a receipt.

@pre_registration_bp.route('/receipt/<string:registration_id>', methods=['GET'])
def pre_registration_confirmation(registration_id):
   status = 'found'
   
   has_session = 'user' in session

   registration = Registration.find_by_id(registration_id)
   if not registration:
      status = 'missing'
      return 'Registration not found'
  
   print(registration)
   return render_template('registration-receipt.html', registration_id=registration_id, status=status, has_session=has_session, registration=registration)

# ---------------------------------------------------------------

@pre_registration_bp.route('/review/<string:registration_id>', methods=['GET'])
@require_auth
def pre_registration_prepare(registration_id):
    
   status = 'found'
   
   registration = Registration.find_by_id(registration_id)
   if not registration:
      status = 'missing'
      return 'Registration not found'
  
   return render_template('registration-review.html', registration_id=registration_id, status=status, registration=registration, user=session.get('user'))

# ---------------------------------------------------------------
# This route GET the registration status. No visible use 
# in the current route pages. Might be used by Kambi?

@pre_registration_bp.route('/check-status/<string:registration_id>', methods=['GET'])
@require_auth
def check_onfido_status(registration_id):
   
   registration = Registration.find_by_id(registration_id)
   if not registration:
      abort(404)
   
   updated = update_check_status(registration)
   return json.dumps(updated.dict(), default=str)  

# ---------------------------------------------------------------

@pre_registration_bp.route('/kyc/init/<string:registration_id>', methods=['PUT'])
@require_auth
def init_kyc_new(registration_id):
   
   # First we get the registration Id.
   registration = Registration.find_by_id(registration_id)
   if not registration:
      abort(404)
    
   print('Got here')  
   print(request.json);
   
   # Put the data into the fields for the processor.
   registration.preferred_language = request.json.get('preferred_language', '')
   registration.loyalty_card_number = request.json.get('loyalty_card_number', '')
   registration.referral_code = request.json.get('referral_code', '')
   
   # Update the fields from the confirmation.
   registration.first_name = request.json.get('first_name', '')
   registration.last_name = request.json.get('last_name', '')
   registration.address_1 = request.json.get('address_1', '')
   registration.address_2 = request.json.get('address_2', '')
   registration.city = request.json.get('city', '')
   registration.state_province = request.json.get('state_province', '')
   registration.country = request.json.get('country', '')
   registration.postal_code = request.json.get('postal_code', '')
   registration.phone_number = request.json.get('phone_number', '')
   registration.email = request.json.get('email', '')

   # Call Onfido to set the applicant Id.
   registration = onfido_run_verification_request_new(registration)
   
   # Now store the user once we know we got here.
   registration.registered_by = session.get('user')['userinfo']['email']
   registration.save()
   
   return json.dumps(registration.dict(), default=str)

# ---------------------------------------------------------------
@pre_registration_bp.route('/kyc/process/<string:registration_id>', methods=['GET'])
@require_auth
def finish_registration_new(registration_id):
   registration = Registration.find_by_id(registration_id)

   if not registration:
      return 'Registration not found'

   onfido_sdk_token = ''

   if registration.kyc_status == 'PENDING':
      onfido_sdk_token = generate_sdk_token(registration.onfido_applicant_id)
   elif registration.kyc_status == 'WAITING_FOR_CHECK_RESPONSE':
      registration = update_check_status(registration)
      print(registration.onfido_check_response)

   return render_template('registration-process.html', registration_id=registration_id, user=session.get('user'), onfido_sdk_token=onfido_sdk_token, registration=registration.safe_serialize())

# ---------------------------------------------------------------

@pre_registration_bp.route('/account-setup/<string:registration_id>', methods=['POST'])
@require_auth
def account_setup(registration_id):
   
   success = False
   registration = Registration.find_by_id(registration_id)
   if not registration:
      return 'Registration not found'
   
   errors = []
   try:
      create_account(registration)
      success = True
      
   except Exception as e:
      print(e)
      errors.append(str(e))
      
   # Ok we return the validation information.
   return jsonify({ 'success': success, 'errors': errors, 'registration_id': registration_id })

# ---------------------------------------------------------------
# Admin features for Registrations.

@pre_registration_bp.route('/list')
@require_auth
def list_registrations():
   return render_template('list.html', user=session.get('user'))
