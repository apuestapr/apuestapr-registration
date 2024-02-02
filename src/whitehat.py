import os
os.environ['MONGO_CONNECTION_STRING'] = 'mongodb+srv://mongo:oJkEEckjc0uO0R2Y@cluster0.nqnmk0a.mongodb.net/?retryWrites=true&w=majority'

from src.models.registration import Registration
import requests
import uuid
import json

"""

CALL: registeruser


{
  "type": "registeruser",
  "brand":"casino21",
  "currency":"EUR",
  "gender":"M",
  "firstname":"Fred",
  "lastname":"Smith",
  "middleName": "John",
  "preferredName": "Freddie",
  "username": "Smith31",
  "salutation":"Mr",
  "dob":"1993-02-01",
  "email":"fred.smith@somecorp.com",
  "phone":"+16175551212",
  "address1":"123 Acacia Avenue",
  "address2":"Suburbia",
  "town":"Oldtown",
  "state":"MT",
  "jurisdiction":"MGA",
  "ssnMatch:"3333", 
  "postalcode":"P098PQ",
  "country":"US",
  "occupatonId": 187,
  "citizenship": "British",
  "employerName": "PBS services",
  "employerAddress": "123 Business Park",
  "employerZip": "60176-2323",
  "employerCity": "Chicago",
  "language":"en",
  "geolocation":"US",
  "securitySettings": {"two-factor-required": true},
  "emitToken": true,
  "fingerprint":"a2fa11cc372a356a30562de1f7a3cc50",
  "userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36",
  "referral":"Google",
  "messagesToAcknowledge":["registration-details", "registration-age", "terms-and-conditions"],
  "enabled":true,
  "promoCode": "promo123"
}

"""

API_URL = os.getenv('WHITEHAT_API_URL')
# API_URL='https://platform.lmg.dev.whg.tech'

whitehat_proxy_username = os.getenv('WHITEHAT_PROXY_USERNAME')
whitehat_proxy_password = os.getenv('WHITEHAT_PROXY_PASSWORD')
whitehat_proxy_ip = os.getenv('WHITEHAT_PROXY_IP')
whitehat_proxy_url = f'http://{whitehat_proxy_username}:{whitehat_proxy_password}@{whitehat_proxy_ip}'
whitehat_proxy = {
    'http': whitehat_proxy_url,
    'https': whitehat_proxy_url
}

print('PROXY:', whitehat_proxy)


def get_player_id(registration: Registration):
    response = requests.post(API_URL + '/platform/usergateway/getuserdetails', json={
        'type': 'getuserdetails',
        'brand': 'liberman',
        'userId': int(registration.whitehat_user_id)
    }).json()

    if response['type'] == 'error':
        raise Exception(response['message'])

    return response['playerid']

def create_account(registration: Registration):
    if not registration.whitehat_user_id:
        response = requests.post(API_URL + '/platform/usergateway/registeruser', json={
            'brand': 'liberman',
            'currency': 'USD',
            'username': str(registration.id),
            'password': str(uuid.uuid4()),
            'firstname': registration.first_name,
            'lastname': registration.last_name,
            'dob': registration.birthday,
            'geolocation': 'US',
            'enabled': True,
            'country': 'US',
            'state': registration.state_province,
            'phone': registration.phone_number,
            'address1': registration.address_1,
            'town': registration.city,
            'postalcode': registration.postal_code,
            'email': registration.email,
            'referral': registration.referral_code,
        })

        print(response.text)

        response.raise_for_status()

        body = response.json()
        if body.get('type', '') == 'error':
            raise Exception('PAM Error for RegisterUser call: ' + json.dumps(body))

        registration.whitehat_user_id = str(body['userid'])
        registration.save()

    # Now set KYC approved
    if not registration.whitehat_kyc_approved:
        body = {
            'userId': int(registration.whitehat_user_id),
            'adminUser': -1,
            'kycApproved': True,
            'reason': 'Successful KYC check by Onfido',
            'brand': 'liberman'
        }
        response = requests.post(API_URL + '/platform/usergateway/set-kyc-approved', json=body)

        body = response.json()

        print('BODY:')
        print(body)
        print('-------------')
        print('RESPONSE:')
        print(response.text)

        response.raise_for_status()

        if body.get('type', '') == 'error':
            raise Exception('PAM Error for SetKYCStatus call: ' + json.dumps(body))
        
        registration.whitehat_kyc_approved = True
        registration.save()
       
        # account_id = create_account_in_whg(registration)
        # manually_approve_kyc(account_id)

        # Send loyalty card number as the username
    pass
    # Hit the API to create the account
    # Then hit the API again to "manually approve" the KYC.