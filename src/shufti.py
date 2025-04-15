import requests, base64, json, hashlib
from random import randint
import uuid
from src.models.registration import Registration, Callback
import datetime
import os
from src.config import Config

url = Config.SHUFTI_API_URL

# Get credentials from Config which loads from environment variables
client_id = Config.SHUFTI_CLIENT_ID
secret_key = Config.SHUFTI_CLIENT_SECRET

app_url = Config.APP_URL

def handle_callback(callback_data):
    """
    Process callback data from Shufti Pro.
    
    Args:
        callback_data: The callback data from Shufti Pro
        
    Returns:
        Registration: The updated registration
    """
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
    """
    Legacy function to start a verification request.
    This is primarily kept for reference and backward compatibility.
    New code should use the KYCFactory.get_service() pattern.
    """
    registration = Registration(
        started_at=datetime.datetime.now()
    )

    registration.save()

    reference = str(registration.id)

    payload = {
        'reference': reference,
        'callback_url': f'{Config.APP_URL}/kyc/callback',
        'language': 'ES',
        'verification_mode': 'any',
        'ttl': 60,
        'document': {
            'supported_types': ['id_card', 'passport', 'driving_license'],
            'allow_offline': '1',
            'allow_online': '1',
        }
    }

    auth = f'{client_id}:{secret_key}'
    b64Val = base64.b64encode(auth.encode()).decode()
    
    response = requests.post(url, 
                    headers={"Authorization": f"Basic {b64Val}", "Content-Type": "application/json"},
                    data=json.dumps(payload))

    # Calculating signature for verification
    calculated_signature = hashlib.sha256(f'{response.content.decode()}{secret_key}'.encode()).hexdigest()
    # Get Shufti Pro Signature
    sp_signature = response.headers.get('Signature','')

    print('CALC SIG:', calculated_signature)
    print('PROVIDED SIG:', sp_signature)
    
    # Convert json string to json object
    json_response = json.loads(response.content)
    updated_registration = handle_callback(json_response)

    return updated_registration
