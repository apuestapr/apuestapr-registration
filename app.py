from flask import Flask, jsonify, render_template, request, abort
from src.shufti import run_verification_request, handle_callback
import json
from src.models.registration import Registration
import pymongo.errors
app = Flask(__name__, static_url_path='/assets', static_folder='assets')


@app.route('/register')
def register():
   return render_template('kyc.html')

@app.route('/register/<string:registration_id>', methods=['GET', 'POST'])
def finish_registration(registration_id):
   registration = Registration.find_by_id(registration_id)

   if not registration:
      return 'Registration not found'
   

   success = False
   errors = []


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

      if registration.kyc_status != 'verification.accepted' and not registration.kyc_override:
         errors.append('You must provide a reason for bypassing KYC')
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
      
      if len(errors) == 0:
         # Look for duplicate loyal card numbers
         dupe = Registration.find_one({
            '_id': {
               '$neq': registration.id,
            },
            'loyal_card_number': {
               '$neq': '',
            }
         })

         if dupe:
            errors.append('Someone has already been registered with this loyalty card number.')
         else:
            registration.complete = True
            registration.save()
            success = True
   
   return render_template('register.html', registration=registration, errors=errors, success=success)




@app.route('/kyc/callback', methods=['POST'])
def kyc_callback():
   handle_callback(request.json)
   return jsonify({
      'status': 'ok'
   })

@app.route('/kyc/init')
def init_kyc():
   registration = run_verification_request()
   return json.dumps(registration.dict(), default=str)

@app.route('/registration/<string:registration_id>')
def get_registration(registration_id):
   """ Returns the registration as JSON """
   registration = Registration.find_by_id(registration_id)
   if not registration:
      abort(404)
   return json.dumps(registration.dict(), default=str)


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
         'message': 'No account found',
      })
   if not registration.complete:
      return jsonify({
         'status': 'error',
         'message': 'Incomplete registration',
      })
   
   # XXX todo: bounce this off of the PAM to get the actual up-to-date information
   return jsonify({
      'status': 'success',
      'payload': {
         'account_id': str(registration.id),
         'first_name': registration.first_name,
      }
   })



if __name__ == '__main__':
   app.run()