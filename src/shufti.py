"""
DEPRECATED MODULE - DO NOT USE FOR NEW CODE

This module is maintained only for backward compatibility.
New code should use the service classes in src.kyc_services instead.

Migration steps:
1. Use KYCFactory.get_service() to get the appropriate service implementation
2. Call methods on the service instance instead of using these functions

Example:
    from src.kyc_factory import KYCFactory
    kyc_service = KYCFactory.get_service()
    registration = kyc_service.init_verification(registration)
    verification_url = kyc_service.generate_client_token(registration)
"""

import logging
logging.warning("Using deprecated module src.shufti - Use src.kyc_services instead")

import requests, base64, json, hashlib
from random import randint
import uuid
from src.models.registration import Registration, Callback
import datetime
import os

url = 'https://api.shuftipro.com/'

# Your Shufti Pro account Client ID
client_id  = 'd8f258ab1770f452ad2f711aad30e7192ead1400a2d3c5148fd432b06d9b7a80'

# Your Shufti Pro account Secret Key
secret_key = '6jaYjSiF6l8E2p1ukRK7qBokewfQOmq5'

# OR Access Token 'access_token = 'YOUR-ACCESS-TOKEN'';

app_url = os.getenv('APP_URL', 'https://localhost:5502')

"""
{
    "reference": "97ee6820-b593-4363-a545-87c18dc9c5f0",
    "event": "verification.accepted",
    "email": null,
    "country": null,
    "verification_data": {
        "document": {
            "country": "US",
            "selected_type": [
                "driving_license"
            ],
            "supported_types": [
                "id_card",
                "passport",
                "driving_license"
            ]
        }
    },
    "verification_result": {
        "document": {
            "document": 1,
            "document_visibility": 1,
            "document_must_not_be_expired": 1,
            "document_proof": null,
            "selected_type": 1
        }
    },
    "info": {
        "agent": {
            "is_desktop": true,
            "is_phone": false,
            "device_name": "Macintosh",
            "browser_name": "Chrome 114.0.0.0",
            "platform_name": "Mac OS 10.15.7"
        },
        "geolocation": {
            "host": "144.121.19.34.lightower.net",
            "ip": "144.121.19.34",
            "rdns": "144.121.19.34",
            "asn": "46887",
            "isp": "Lightower Fiber Networks I LLC",
            "country_name": "United States",
            "country_code": "US",
            "region_name": "Massachusetts",
            "region_code": "MA",
            "city": "Boston",
            "postal_code": "02111",
            "continent_name": "North America",
            "continent_code": "NA",
            "latitude": "42.352951049805",
            "longitude": "-71.057899475098",
            "metro_code": "",
            "timezone": "America/New_York",
            "ip_type": "ipv4",
            "capital": "Washington D.C.",
            "currency": "USD"
        }
    }
}
"""
def handle_callback(callback_data):
    if 'reference' not in callback_data:
        raise KeyError('Reference not in callback data')
    
    reference = callback_data['reference']

    registration = Registration.find_by_id(reference)
    if not registration:
        raise Exception('Registration not found')
    
    registration.callbacks.append(Callback(
        timestamp=datetime.datetime.utcnow(),
        body=callback_data,
    ))

    registration.kyc_status = callback_data['event']
    registration.save()

    return registration

def run_verification_request():
    registration = Registration(
        # Was set to utcnow
        started_at=datetime.datetime.now()
    )

    registration.save()

    reference = str(registration.id)

    payload = {
        'reference': reference,
        'callback_url': f'{os.getenv("APP_URL")}/kyc/callback', # TODO: Update the link that is being used here. It would cause a 500 status error code when run on Render otherwise...
        #
        # Need to use this, or they will not allow the callback. 
        # TODO: Need access to the onfideo
        # 'callback_url': f'{os.getenv("RENDER_EXTERNAL_URL")}/kyc/callback',
        # 'country': 'PR',
        #
        'language': 'ES',
        'verification_mode': 'any',
        'ttl': 60,
        'document': {
            'supported_types': ['id_card', 'passport', 'driving_license'],
            'allow_offline': '1',
            'allow_online': '1',
        }
    }

    auth = '{}:{}'.format(client_id, secret_key)
    b64Val = base64.b64encode(auth.encode()).decode()
    # if access token 
    # b64Val = access_token
    # replace "Basic with "Bearer" in case of Access Token
    response = requests.post(url, 
                    headers={"Authorization": "Basic %s" % b64Val, "Content-Type": "application/json"},
                    data=json.dumps(payload))

    # Calculating signature for verification
    # calculated signature functionality cannot be implement in case of access token
    calculated_signature = hashlib.sha256('{}{}'.format(response.content.decode(), secret_key).encode()).hexdigest()
    # Get Shufti Pro Signature
    sp_signature = response.headers.get('Signature','')

    print('CALC SIG:', calculated_signature)
    print('PROVIDED SIG:', sp_signature)
    # Convert json string to json object
    json_response = json.loads(response.content)
    updated_registration = handle_callback(json_response)


    return updated_registration
   
# verification_request = {
#     'reference'         :   'ref-{}{}'.format(randint(1000, 9999), randint(1000, 9999)),
#     'country'           :   'GB', 
#     'language'          :   'EN',
#     'email'             :   'test@test.com',
#     'callback_url'      :   'https://yourdomain.com/profile/notifyCallback',
#     'verification_mode' :   'any',
#     'ttl'               :    60,
# }
# # Use this key if you want to perform document verification with OCR
# verification_request['document'] = {
#     'proof'             :   '',
#     'additional_proof'  :   '',
#     'name'              :   '',
#     'dob'               :   '',
#     'age'               :   '',
#     'document_number'   :   '',
#     'expiry_date'       :   '',
#     'issue_date'        :   '',
#     'allow_offline'     :   '1',
#     'allow_online'      :   '1',
#     'supported_types'   :   ['id_card','passport'],
#     'gender'   : ''
# }
# # Use this key want to perform address verification with OCR
# verification_request['address'] = {
#     'proof'             :   '',
#     'name'              :   '',
#     'full_address'      :   '',
#     'address_fuzzy_match' : '1',
#     'issue_date'        :   '',
#     'supported_types'   :   ['utility_bill','passport','bank_statement']
# }

# Calling Shufti Pro request API using python  requests
