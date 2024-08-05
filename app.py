from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, render_template, request, abort, url_for, session, redirect
from src.shufti import run_verification_request, handle_callback
from src.onfido import run_verification_request as onfido_run_verification_request, update_check_status, generate_sdk_token, run_check
from src.onfido import run_verification_request_new as onfido_run_verification_request_new

from authlib.integrations.flask_client import OAuth
from urllib.parse import quote_plus, urlencode
from datetime import date
import dateutil.parser as dparser
import json
from src.models.registration import Registration
import pymongo.errors
import os
import sys 
from functools import wraps
from src.whitehat import create_account, get_player_id
from bson import json_util
from bson.objectid import ObjectId
from datetime import datetime
from src.blueprints.pre_registration import pre_registration_bp
from src.blueprints.registration import registration_bp
from src.blueprints.qr_code import qr_code_bp

app = Flask(__name__, static_url_path='/assets', static_folder='assets')

app.secret_key = os.getenv('APP_SECRET_KEY')

oauth = OAuth(app)

# ---------------------------------------------------------------
# Setup the OAuth Registry with the Information needed.

oauth.register(
    "auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# ---------------------------------------------------------------
# Define a function to require an endpoint to have an OAuth
# User. This ensures that we know who the person is.

def require_auth(f):
   @wraps(f)
   def decorated_function(*args, **kwargs):
      user = session.get('user')
      if not user:
         return redirect('/login')
      return f(*args, **kwargs)
   return decorated_function

# ---------------------------------------------------------------
# Setup the Login Route.

@app.route('/login')
def login():
   return oauth.auth0.authorize_redirect(
      redirect_uri=url_for('auth0_callback', _external=True)
   )

# ---------------------------------------------------------------
# Setup the OAuth callback.

@app.route("/auth0/callback", methods=["GET", "POST"])
def auth0_callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

# ---------------------------------------------------------------
# Setup the Logout.

@app.route("/logout")
@require_auth
def logout():
    session.clear()
    return redirect(
        "https://" + os.getenv("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": os.getenv("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# ---------------------------------------------------------------
# Set up the default home route.
@app.route('/')
@require_auth
def home():
   return render_template('home.html', user=session.get('user'))

# ---------------------------------------------------------------

@app.route('/register')
@require_auth
def register():
   return render_template('kyc.html', user=session.get('user'))

# ---------------------------------------------------------------
# Helper function to calculate a user age.

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
# This is a GET/POST route that find by a Registration Id and 
# then starts the KYC process.

@app.route('/register/<string:registration_id>', methods=['GET', 'POST'])
@require_auth
def finish_registration(registration_id):
   registration = Registration.find_by_id(registration_id)

   if not registration:
      return 'Registration not found'

   success = False
   errors = []
   onfido_sdk_token = ''

   print("DUMP", json.dumps(registration.onfido_reports))
   print(registration.kyc_status)
   
   if registration.kyc_status == 'PENDING':
      onfido_sdk_token = generate_sdk_token(registration.onfido_applicant_id)

   elif registration.kyc_status == 'WAITING_FOR_CHECK_RESPONSE':
      registration = update_check_status(registration)

      print(registration.onfido_check_response)

   if request.method == 'POST':
      print(request.form)

      # For the preRegistrationId in case we need to delete it.
      preRegistrationId = request.form['preRegistrationId']
      
      # Process the incoming data
      registration.first_name = request.form['first_name'].strip()
      registration.last_name = request.form['last_name'].strip()
      registration.loyalty_card_number = request.form['loyalty_card_number'].strip()
      registration.email = request.form['email'].strip()
      registration.phone_number = request.form['phone_number'].strip()
      registration.birthday = request.form['birthday'].strip()
      registration.kyc_override = request.form.get('kyc_override', '').strip()
      registration.address_1 = request.form.get('address_1', '').strip()
      registration.address_2 = request.form.get('address_2', '').strip()
      registration.city = request.form.get('city', '').strip()
      registration.state_province = request.form.get('state_province', '').strip()
      registration.postal_code = request.form.get('postal_code', '').strip()
      registration.country = request.form.get('country', '').strip()
      registration.referral_code = request.form.get('referral_code', '').strip()

      if request.form.get('agree_to_terms', None):
         registration.agree_to_terms = True
      else:
         registration.agree_to_terms = False

      if registration.kyc_status != 'COMPLETE' and not registration.kyc_override:
         errors.append('Debe proporcionar una razón para omitir la verificación KYC.')
      if not registration.first_name:
         errors.append('Nombre de pila es obligatorio.')
      if not registration.last_name:
         errors.append('Apellido es obligatorio.')
      if not registration.loyalty_card_number:
         errors.append('Número de Tarjeta de Jugador es obligatorio.')
      if not registration.email:
         errors.append('Email es obligatorio.')
      if not registration.phone_number:
         errors.append('El número de teléfono es obligatorio.')
      if not registration.referral_code:
         errors.append('El código de referencia es obligatorio.')

      if not registration.birthday:
         errors.append('Birthday is required')
      
      bday = dparser.parse(registration.birthday).date()

      if calculateAge(bday) < 18:
         errors.append('Debe tener al menos 18 años de edad para apostar en Puerto Rico.')

      if not registration.agree_to_terms:
         errors.append('Debe aceptar los términos y condiciones.')

      if not registration.address_1 or not registration.city or not registration.state_province or not registration.country or not registration.postal_code:
         print(registration)
         errors.append('Direccion es obligatorio')
      
      if len(errors) == 0:
         # Look for duplicate loyal card numbers
         dupe_card_number = Registration.find_one({
            '_id': {
               '$ne': registration.id,
            },
            'loyal_card_number': registration.loyalty_card_number
         })

         dupe_email = Registration.find_one({
            '_id': {
               '$ne': registration.id,
            },
            'email': registration.email
         })

         # Register with white hat
         
         if dupe_card_number:
            # Someone has already been registered with this loyalty card number.
            errors.append('Alguien ya ha sido registrado con este número de tarjeta de fidelidad.')
         elif dupe_email:
            # Someone has already been registered with this email address.
            errors.append('Alguien ya ha sido registrado con esta dirección de correo electrónico.')
         else:    
            if registration.whitehat_user_id == '' or not registration.whitehat_kyc_approved:
               try:
                  create_account(registration)
               except Exception as e:
                  errors.append(str(e))
            if len(errors) == 0:
               registration.complete = True
               registration.save()
         
               success = True
   
   return render_template('register.html', user=session.get('user'), onfido_sdk_token=onfido_sdk_token, registration=registration, errors=errors, success=success)

# ---------------------------------------------------------------
@app.route('/pre_registration/validate/<string:registration_id>', methods=['POST'])
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
   
   dupe_card_number = Registration.find_one({ '_id': { '$ne': registration_id, }, 'loyal_card_number': loyalty_card_number })
   dupe_email = Registration.find_one({ '_id': { '$ne': registration_id, }, 'email': email })
       
   print('is Dup')
   print(dupe_card_number);
     
   if dupe_email:
      errors.append('Alguien ya ha sido registrado con esta dirección de correo electrónico.')
      
   if dupe_card_number:
      # Someone has already been registered with this loyalty card number.
      errors.append('Alguien ya ha sido registrado con este número de tarjeta de fidelidad.')
            
   # ----------------------------------------------------------------
   if len(errors) == 0:
      success = True
   
   # Ok we return the validation information.
   return jsonify({ 'success': success, 'errors': errors, 'registration_id': registration_id })

# ---------------------------------------------------------------
# This is the KYC callback once the process is done.
@app.route('/kyc/callback', methods=['POST'])
@require_auth
def kyc_callback():
   handle_callback(request.json)
   return jsonify({
      'status': 'ok'
   })

# ---------------------------------------------------------------
# This is the init process for the KYC process. This 
# is called by the [KYC.html] page.

@app.route('/kyc/init', methods=['POST'])
@require_auth
def init_kyc():
   # registration = run_verification_request()
   preferred_language = request.json.get('preferred_language', '')
   registration = onfido_run_verification_request()
   registration.preferred_language = preferred_language
   registration.registered_by = session.get('user')['userinfo']['email']
   registration.save()
   return json.dumps(registration.dict(), default=str)


# TOD_ Move to New Version.


# ---------------------------------------------------------------
# This is a route that returns a single registration.
# It is called by the register.html page.

@app.route('/registration/<string:registration_id>')
@require_auth
def get_registration(registration_id):
   """ Returns the registration as JSON """
   registration = Registration.find_by_id(registration_id)
   if not registration:
      abort(404)
   return json.dumps(registration.dict(), default=str)

# ---------------------------------------------------------------
# This function is called via a POST from the /register.html file
# Need more info.

@app.route('/registration/<string:registration_id>/run-check', methods=['POST'])
@require_auth
def run_onfido_check(registration_id):
   
   # Load the registration person.
   registration = Registration.find_by_id(registration_id)
   if not registration:
      abort(404)
   
   # Get the document_ids from the post.
   document_ids = request.json['document_ids']

   # Update the Registraiton with the new document ids.
   registration.onfido_document_ids = document_ids
   
   # Now run the check.
   registration_with_check = run_check(registration)
   
   return json.dumps(registration_with_check.dict(), default=str) 

# ---------------------------------------------------------------
# This route get the Kambi OTC. Need more information.
# No visible use in the HTML templates. Might be used by 
# Kambi for OTC uses?

@app.route('/kambi/otc', methods=['GET'])
def kambi_otc_iframe():
   """ Renders the iframe for the Kambi kiosk """
   return render_template('otc-iframe.html')

# ---------------------------------------------------------------
# This route GET the Kambi SSL. Need more information on 
# how this fits into the process.

@app.route('/kambi/sst', methods=['GET'])
def kambi_sst_iframe():
   """ Renders the iframe for the Kambi kiosk """
   return render_template('sst-iframe.html')

# ---------------------------------------------------------------
# This has something to do with exchanging a users kami loyalty_card_number
# for something else.

@app.route('/kambi/exchange/<string:loyalty_card_number>', methods=['GET'])
def exchange_loyalty_card_for_kiosk(loyalty_card_number: str):
   # XXX todo: need to lock this down bc anyone could brute force the API to try to look up PII with random loyalty card numbers.
   registration = Registration.find_one({
      'loyalty_card_number': loyalty_card_number,
   })

   if not registration:
      return jsonify({
         'status': 'error',
         'message': 'No account found. Please try again.',
      })
   if not registration.complete:
      return jsonify({
         'status': 'error',
         'message': 'Registration incomplete. Please see an associate to complete your registration.',
      })
   
   # XXX todo: bounce this off of the PAM to get the actual up-to-date information
   try:
      if not registration.whitehat_playerid:
         registration.whitehat_playerid = str(get_player_id(registration))
         registration.save()
   except Exception as e:
      return jsonify({
         'status': 'error',
         'message': str(e)
      })
   return jsonify({
      'status': 'success',
      'payload': registration.safe_serialize()
   })

# ---------------------------------------------------------------
# Register the Pre-Registration Routes that are going to be 
# used to drive the list.html page that allows staff to manage
# users who have setup their account information ahead of time.

app.register_blueprint(pre_registration_bp, url_prefix='/registration')
app.register_blueprint(registration_bp, url_prefix='/registrations')
app.register_blueprint(qr_code_bp, url_prefix='/qr_code')

if __name__ == '__main__':
   app.run()
   