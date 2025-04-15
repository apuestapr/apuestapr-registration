from flask import Blueprint, request, jsonify, render_template, abort, session, redirect
from src.models.registration import Registration, serialize_documents
from src.shufti import run_verification_request, handle_callback
from src.onfido import run_verification_request as onfido_run_verification_request, update_check_status, generate_sdk_token, run_check
# from src.onfido import run_verification_request_new as onfido_run_verification_request_new
from src.whitehat import create_account, get_player_id
import dateutil.parser as dparser
from datetime import date

import json
from bson.objectid import ObjectId
# from datetime import datetime
from functools import wraps
from src.models.registration import Registration
import datetime

# Import the KYC factory instead of specific provider functions
from src.kyc_factory import KYCFactory
from src.config import FeatureFlags

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

def calculateAge(born):
    today = date.today()
    try: 
        birthday = born.replace(year = today.year)
 
    # raised when birth date is February 29
    # and the current year is not a leap year
    except ValueError: 
        birthday = born.replace(year = today.year,
                  month = born.month + 1, day = 1)
 
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year
     
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

# ---------------------------------------------------------------
@pre_registration_bp.route('/create', methods=['POST'])
def create_pre_registration():
   try:
      data = request.get_json()
      if not data:
        return jsonify({'msg': 'No data provided'}), 400

      if not data:
        return jsonify({'msg': 'No data provided'}), 400
            
      pre_reg = Registration(**data)
      # Make the email lowercase.
      pre_reg.email = pre_reg.email.lower().strip()
      pre_reg.started_at = datetime.datetime.now()
      
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
# This is the route for the registration form that a 
# public (non-authenticated) user will need to get started in ENGLISH.

@pre_registration_bp.route('/start-en')
def start_pre_registration_en():
   return render_template('registration-start-en.html')

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

@pre_registration_bp.route('/validate/<string:registration_id>', methods=['POST'])
@require_auth
def validate_kyc_process(registration_id):
   
   registration = Registration.find_by_id(registration_id)
   if not registration:
      return 'Registration not found'

   success = False
   errors = []

   first_name = request.json.get('first_name', '')
   last_name = request.json.get('last_name', '')
   email = request.json.get('email', '')
   phone_number = request.json.get('phone_number', '')
   address_1 = request.json.get('address_1', '')
   city = request.json.get('city', '')
   state_province = request.json.get('state_province', '')
   postal_code = request.json.get('postal_code', '')
   country = request.json.get('country', '')
   birthday = request.json.get('birthday', '')
   loyalty_card_number = request.json.get('loyalty_card_number', '')
   referral_code = request.json.get('referral_code', '')
   
   if not first_name:
      errors.append('Nombre de pila es obligatorio.')
      
   if not last_name:
      errors.append('Apellido es obligatorio.')
      
   if not loyalty_card_number:
      errors.append('Número de Tarjeta de Jugador es obligatorio.')
      
   if not email:
      errors.append('Email es obligatorio.')
      
   if not phone_number:
      errors.append('El número de teléfono es obligatorio.')
      
   if not referral_code:
      errors.append('El código de referencia es obligatorio.')

   # ----------------------------------------------------------------
   # Validate the address, again.
   
   if not address_1 or not city or not state_province or not country or not postal_code:
      errors.append('Direccion es obligatorio')
         
   # ----------------------------------------------------------------
   # Lets make sure the dateof birth is valid.

   if not birthday:
      errors.append('Birthday is required')
   else:
      bday = dparser.parse(birthday).date()
      if calculateAge(bday) < 18:
         errors.append('Debe tener al menos 18 años de edad para apostar en Puerto Rico.')
  
   # ----------------------------------------------------------------
   # Ok lets check that the email and the loyal_card_number
   # have not been used already.
   
   email = email.lower().strip()
   loyalty_card_number = loyalty_card_number.strip()
   object_id = ObjectId(registration_id)
   
   # Query the MongoDB.
   dupe_card_number = Registration.find_one({ '_id': { '$ne': object_id, }, 'loyal_card_number': loyalty_card_number })
   dupe_email = Registration.find_one({ '_id': { '$ne': object_id }, 'email': email })
   
   if dupe_email:
      # Someone has already used this email address
      errors.append('kAlguien ya ha sido registrado con esta dirección de correo electrónico.')
      
   if dupe_card_number:
      # Someone has already been registered with this loyalty card number.
      errors.append('Alguien ya ha sido registrado con este número de tarjeta de fidelidad.')
            
   # ----------------------------------------------------------------
   if len(errors) == 0:
      success = True
   
   # Ok we return the validation information.
   return jsonify({ 'success': success, 'errors': errors, 'registration_id': registration_id })

# ---------------------------------------------------------------
# This function is called via a POST from the /register.html file
# Need more info.

@pre_registration_bp.route('/run-check/<string:registration_id>', methods=['POST'])
@require_auth
def run_onfido_check(registration_id):
   
   # Load the registration person.
   registration = Registration.find_by_id(registration_id)
   if not registration:
      return jsonify({
         'success': False,
         'errors': ['Registration not found']
      }), 200
   
   data = request.json
   if not data or not data.get('document_ids'):
      return jsonify({
         'success': False,
         'errors': ['No document IDs provided']
      }), 200
   
   document_ids = data.get('document_ids')
   try:
      # Use the KYC factory to process documents with the appropriate service
      kyc_service = KYCFactory.get_service()
      registration = kyc_service.process_documents(registration, document_ids)
      
      return jsonify({
         'success': True
      }), 200
   except Exception as e:
      print(e, file=sys.stderr)
      return jsonify({
         'success': False,
         'errors': [str(e)]
      }), 200

# ---------------------------------------------------------------
# This route GET the registration status. No visible use 
# in the current route pages. Might be used by Kambi?

@pre_registration_bp.route('/check-status/<string:registration_id>', methods=['GET'])
@require_auth
def check_onfido_status(registration_id):
   
   registration = Registration.find_by_id(registration_id)
   if not registration:
      return "Registration not found", 404
   
   # Use the KYC factory to update the status with the appropriate service
   kyc_service = KYCFactory.get_service()
   updated = kyc_service.update_status(registration)
   return json.dumps(updated.dict(), default=str)

# ---------------------------------------------------------------

@pre_registration_bp.route('/kyc/init/<string:registration_id>', methods=['PUT'])
@require_auth
def init_kyc_new(registration_id):
   
   # First we get the registration Id.
   registration = Registration.find_by_id(registration_id)
   if not registration:
      abort(404)

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
   
   # Make the email lowercase. This keeps things tight
   # so we do not get dups.
   registration.email = registration.email.lower().strip()

   # Initialize KYC verification using the appropriate service
   kyc_service = KYCFactory.get_service()
   registration = kyc_service.init_verification(registration)
   
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

   # Get the KYC service based on the feature flag or registration's provider
   kyc_service = KYCFactory.get_service()
   
   # Default values
   client_token = ''
   verification_url = ''
   
   if registration.kyc_status == 'PENDING':
      # Generate the client token or verification URL for the appropriate provider
      if FeatureFlags.is_shufti_enabled() or registration.kyc_provider == 'shufti':
         verification_url = kyc_service.generate_client_token(registration)
      else:
         # Legacy Onfido flow
         client_token = kyc_service.generate_client_token(registration)
   elif registration.kyc_status == 'WAITING_FOR_CHECK_RESPONSE':
      # Update the verification status
      registration = kyc_service.update_status(registration)

   # Determine which template to use based on the KYC provider
   if FeatureFlags.is_shufti_enabled() or registration.kyc_provider == 'shufti':
      return render_template(
         'registration-process-shufti.html',  # New template for Shufti iframe
         registration_id=registration_id,
         user=session.get('user'),
         verification_url=verification_url,
         registration=registration.safe_serialize()
      )
   else:
      # Legacy Onfido template
      return render_template(
         'registration-process.html',
         registration_id=registration_id,
         user=session.get('user'),
         onfido_sdk_token=client_token,
         registration=registration.safe_serialize()
      )

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

# ---------------------------------------------------------------

@pre_registration_bp.route('/email/<string:email>', methods=['GET'])
def validate_email_only(email):
 
   # Clean the email string.
   email = email.lower().strip()

   # Look for the of results.
   result = Registration.find_one({ 'email': email })    

   return jsonify({ 
      'isEmailUsed': result is not None, 
      'email': email
   }), 200

# ---------------------------------------------------------------
# New endpoint to check KYC status for the iframe polling approach
@pre_registration_bp.route('/kyc/check-status/<string:registration_id>', methods=['GET'])
def check_kyc_status(registration_id):
    """
    Endpoint to check the status of a registration's KYC verification.
    Used by the frontend to poll for status changes.
    """
    try:
        # Find the registration by ID
        registration = Registration.find_by_id(registration_id)
        
        if not registration:
            return jsonify({
                "success": False,
                "error": "Registration not found"
            }), 404
            
        # Return the current status
        return jsonify({
            "success": True,
            "status": registration.kyc_status,
            "complete": registration.complete
        }), 200
        
    except Exception as e:
        print(f"Error checking KYC status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# New endpoint to handle Shufti Pro redirects after verification
@pre_registration_bp.route('/kyc/status/<string:registration_id>', methods=['GET'])
def kyc_status_redirect(registration_id):
    """
    Endpoint to handle redirects from Shufti Pro after verification.
    This route checks the current verification status and renders the appropriate page.
    
    This route intentionally doesn't require authentication to handle redirects 
    from Shufti Pro on mobile devices where the user might not be authenticated.
    """
    try:
        # Find the registration by ID
        registration = Registration.find_by_id(registration_id)
        
        if not registration:
            return jsonify({
                "success": False,
                "error": "Registration not found"
            }), 404
            
        # Use the KYC factory to update the status with the appropriate service
        kyc_service = KYCFactory.get_service()
        updated_registration = kyc_service.update_status(registration)
        
        # We no longer check callbacks since we're not storing them
        # Instead, just rely on the current kyc_status value
        
        # Get user from session if available, otherwise provide a default
        user = session.get('user') if session.get('user') else None
        
        # Render the Shufti process template with the current status
        return render_template(
            'registration-process-shufti.html',
            registration_id=registration_id,
            user=user,
            verification_url='',  # No verification URL needed for status page
            registration=updated_registration.safe_serialize()
        )
        
    except Exception as e:
        print(f"Error handling KYC status redirect: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ---------------------------------------------------------------
# Endpoint to update registration fields directly (for admin use)
@pre_registration_bp.route('/db-update/<string:registration_id>', methods=['POST'])
@require_auth
def update_registration_fields(registration_id):
    """
    Updates specific fields in a registration document.
    Only certain fields are allowed to be updated for security.
    """
    try:
        # Find the registration by ID
        registration = Registration.find_by_id(registration_id)
        
        if not registration:
            return jsonify({
                "success": False,
                "error": "Registration not found"
            }), 404
        
        # Get the data to update
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # List of fields that are allowed to be updated
        allowed_fields = ['kyc_status', 'shufti_reference']
        updated_fields = []
        
        # Update only allowed fields
        for field in allowed_fields:
            if field in data:
                setattr(registration, field, data[field])
                updated_fields.append(field)
        
        # If we're resetting to PENDING, log the action but don't add to callbacks
        if 'kyc_status' in data and data['kyc_status'] == 'PENDING':
            # Log the reset action instead of storing it
            user_email = session.get('user', {}).get('userinfo', {}).get('email', 'unknown')
            print(f"Reset verification for registration {registration_id} by {user_email}")
        
        # Save the changes
        if updated_fields:
            registration.save()
            
        return jsonify({
            "success": True,
            "message": f"Updated fields: {', '.join(updated_fields)}"
        }), 200
        
    except Exception as e:
        print(f"Error updating registration: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
