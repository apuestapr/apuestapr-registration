from dotenv import load_dotenv
# Explicitly load from .flaskenv
load_dotenv('.flaskenv')

import os
# Log the loaded environment variables for debugging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"APP_URL loaded in app.py: {os.getenv('APP_URL')}")
logger.info(f"KYC_PROVIDER loaded in app.py: {os.getenv('KYC_PROVIDER')}")

from flask import Flask, jsonify, render_template, request, abort, url_for, session, redirect
from src.shufti import handle_callback

from authlib.integrations.flask_client import OAuth
from urllib.parse import quote_plus, urlencode
from datetime import date
import dateutil.parser as dparser
import json
from src.models.registration import Registration
import pymongo.errors
import sys 
from functools import wraps
from src.whitehat import create_account, get_player_id
from bson import json_util
from bson.objectid import ObjectId
from datetime import datetime
from src.blueprints.pre_registration import pre_registration_bp
from src.blueprints.registration import registration_bp
from src.blueprints.qr_code import qr_code_bp
from src.kyc_factory import KYCFactory

app = Flask(__name__, static_url_path='/assets', static_folder='assets')

app.secret_key = os.getenv('APP_SECRET_KEY')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
# LEGACY 

@app.route('/register')
@require_auth
def register():
   return render_template('kyc.html', user=session.get('user'))

# ---------------------------------------------------------------
# Helper function to calculate a user age.

# def calculateAge(born):
    
# This is a GET/POST route that find by a Registration Id and 
# then starts the KYC process.
#

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
   
   # XXX todo: need to lock this down bc anyone could brute force the API to try 
   # to look up PII with random loyalty card numbers.
   
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

# ---------------------------------------------------------------
# Shufti Pro callback endpoint
# This endpoint receives callbacks from Shufti Pro about verification status
@app.route('/kyc/shufti-callback', methods=['POST'])
def shufti_callback():
    logger.info("Received callback from Shufti")
    
    # Log headers and body for debugging
    if request.headers:
        logger.info(f"Received callback from Shufti (headers): {dict(request.headers)}")
    
    # Get the callback data
    data = request.json
    if data:
        logger.info(f"Received callback from Shufti (body): {data}")
    else:
        logger.error("No data received in Shufti callback")
        return jsonify({"success": False, "error": "No data received"}), 400
    
    # Process the callback with our KYC service
    kyc_service = KYCFactory.get_service()
    registration = kyc_service.process_callback(data)
    
    if not registration:
        logger.error("Failed to process Shufti callback - no registration found")
        # Return 200 anyway to prevent Shufti from retrying
        return jsonify({"success": False, "error": "Registration not found"}), 200
    
    logger.info(f"Successfully processed Shufti callback for registration {registration.id}")
    return jsonify({"success": True}), 200

if __name__ == '__main__':
   app.run()
   