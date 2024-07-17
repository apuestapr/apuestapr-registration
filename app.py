from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, render_template, request, abort, url_for, session, redirect
from src.shufti import run_verification_request, handle_callback
from src.onfido import run_verification_request as onfido_run_verification_request, update_check_status, generate_sdk_token, run_check
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
app = Flask(__name__, static_url_path='/assets', static_folder='assets')

print(f"APP_SECRET_KEY: {os.getenv('AUTH0_CLIENT_ID')}")

app.secret_key = os.getenv('APP_SECRET_KEY')

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

def require_auth(f):
   @wraps(f)
   def decorated_function(*args, **kwargs):
      user = session.get('user')
      if not user:
         return redirect('/login')
      return f(*args, **kwargs)
   return decorated_function


@app.route('/login')
def login():
   return oauth.auth0.authorize_redirect(
      redirect_uri=url_for('auth0_callback', _external=True)
   )

@app.route("/auth0/callback", methods=["GET", "POST"])
def auth0_callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

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

@app.route('/')
@require_auth
def home():
   return render_template('home.html', user=session.get('user'))



@app.route('/list')
@require_auth
def list():
   return render_template('list.html', user=session.get('user'))



@app.route('/register')
@require_auth
def register():
   return render_template('kyc.html', user=session.get('user'))


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

@app.route('/register/<string:registration_id>', methods=['GET', 'POST'])
@require_auth
def finish_registration(registration_id):
   registration = Registration.find_by_id(registration_id)

   if not registration:
      return 'Registration not found'



   

   success = False
   errors = []

   onfido_sdk_token = ''

   print(json.dumps(registration.onfido_reports))

   if registration.kyc_status == 'PENDING':
      onfido_sdk_token = generate_sdk_token(registration.onfido_applicant_id)

   elif registration.kyc_status == 'WAITING_FOR_CHECK_RESPONSE':
      registration = update_check_status(registration)

      print(registration.onfido_check_response)

   if request.method == 'POST':
      print(request.form)


      # Process the incoming data
      registration.first_name = request.form['first_name']
      registration.last_name = request.form['last_name']
      registration.loyalty_card_number = request.form['loyalty_card_number']
      registration.email = request.form['email']
      registration.phone_number = request.form['phone_number']
      registration.birthday = request.form['birthday']
      registration.kyc_override = request.form.get('kyc_override', '')
      registration.address_1 = request.form.get('address_1', '')
      registration.address_2 = request.form.get('address_2', '')
      registration.city = request.form.get('city', '')
      registration.state_province = request.form.get('state_province', '')
      registration.postal_code = request.form.get('postal_code', '')
      registration.country = request.form.get('country', '')
      registration.referral_code = request.form.get('referral_code', '')

      if request.form.get('agree_to_terms', None):
         registration.agree_to_terms = True
      else:
         registration.agree_to_terms = False

      if registration.kyc_status != 'COMPLETE' and not registration.kyc_override:
         errors.append('You must provide a reason for bypassing KYC')
      if not registration.loyalty_card_number:
         errors.append('Loyalty card number is required')
      if not registration.first_name:
         errors.append('First name is required')
      if not registration.last_name:
         errors.append('Last name is required')
      if not registration.loyalty_card_number:
         errors.append('Loyalty card number is required')
      if not registration.email:
         errors.append('Email is required')
      if not registration.phone_number:
         errors.append('Phone is required')

      if not registration.birthday:
         errors.append('Birthday is required')
      
      bday = dparser.parse(registration.birthday).date()

      if calculateAge(bday) < 18:
         errors.append('You must be at least 18 years of age to bet in Puerto Rico.')

      if not registration.agree_to_terms:
         errors.append('You must agree to the terms and conditions')

      if not registration.address_1 or not registration.city or not registration.state_province or not registration.country or not registration.postal_code:
         print(registration)
         errors.append('Address is required')
      
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
            errors.append('Someone has already been registered with this loyalty card number.')
         elif dupe_email:
            errors.append('Someone has already been registered with this email address.')
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




@app.route('/kyc/callback', methods=['POST'])
@require_auth
def kyc_callback():
   handle_callback(request.json)
   return jsonify({
      'status': 'ok'
   })

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

@app.route('/registration/<string:registration_id>')
@require_auth
def get_registration(registration_id):
   """ Returns the registration as JSON """
   registration = Registration.find_by_id(registration_id)
   if not registration:
      abort(404)
   return json.dumps(registration.dict(), default=str)

@app.route('/registration/<string:registration_id>/run-check', methods=['POST'])
@require_auth
def run_onfido_check(registration_id):
   registration = Registration.find_by_id(registration_id)
   if not registration:
      abort(404)
   document_ids = request.json['document_ids']

   registration.onfido_document_ids = document_ids
   
   registration_with_check = run_check(registration)
   return json.dumps(registration_with_check.dict(), default=str) 


@app.route('/registration/<string:registration_id>/check-status', methods=['GET'])
@require_auth
def check_onfido_status(registration_id):
   registration = Registration.find_by_id(registration_id)
   if not registration:
      abort(404)
   
   updated = update_check_status(registration)
   return json.dumps(updated.dict(), default=str)  


   


@app.route('/kambi/otc', methods=['GET'])
def kambi_otc_iframe():
   """ Renders the iframe for the Kambi kiosk """
   return render_template('otc-iframe.html')

@app.route('/kambi/sst', methods=['GET'])
def kambi_sst_iframe():
   """ Renders the iframe for the Kambi kiosk """
   return render_template('sst-iframe.html')

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

users = [
    {'id': 1, 'date': '1/1/2024', 'name': 'John Doe', 'email': 'john@example.com', 'phone': '11111', "address": '2 Main Street'},
    {'id': 2, 'date': '1/1/2024', 'name': 'Jane Smith', 'email': 'jane@example.com', 'phone': '11111', 'address': '2 Main Street'},
    {'id': 3, 'date': '1/1/2024', 'name': 'Michael Johnson', 'email': 'michael@example.com', 'phone': '11111', 'address': '2 Main Street'},
]

@app.route('/list/all', methods=['GET'])
def list_all_users():
    return jsonify(users), 200
    
@app.route('/list/delete/<int:id>', methods=['DELETE'])
def delete_user(id):
    global users
    user_to_delete = next((user for user in users if user['id'] == id), None)
    if user_to_delete:
        users = [user for user in users if user['id'] != id]
        return jsonify({'message': f'User with id {id} deleted successfully'}), 200
    else:
        return jsonify({'message': f'User with id {id} not found'}), 404


if __name__ == '__main__':
   app.run()