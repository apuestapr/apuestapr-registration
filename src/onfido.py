import onfido
import os
from src.models.registration import Registration, Callback
import datetime
from onfido.regions import Region
from src.config import Config

api = onfido.Api(Config.ONFIDO_API_KEY, region=Region.US)

def generate_sdk_token(applicant_id: str):
    """
    Generate an SDK token for the Onfido client.
    
    Args:
        applicant_id: The applicant ID to generate the token for
        
    Returns:
        str: The generated token
    """
    response = api.sdk_token.generate({
        'applicant_id': applicant_id,
    })

    return response['token']

def run_verification_request(registration):
    """
    Start a verification request for a registration.
    
    Args:
        registration: The registration to verify
        
    Returns:
        Registration: The updated registration
    """
    registration.started_at = datetime.datetime.now()
    registration.save()
    
    applicant_details = {
        'first_name': registration.first_name or 'ApuestaPR',
        'last_name': registration.last_name or 'Customer',
        'dob': registration.birthday or '1984-01-01',
        'address': {
            'street': 'Second Street',
            'town': 'London',
            'postcode': 'S2 2DF',
            'country': 'GBR'
        },
        'location': {
            'ip_address': '127.0.0.1',
            'country_of_residence': 'GBR'
        }
    }

    response = api.applicant.create(applicant_details)
    registration.onfido_applicant_id = response['id']
    registration.save()

    return registration

def run_check(registration):
    """
    Run a check on a registration.
    
    Args:
        registration: The registration to check
        
    Returns:
        Registration: The updated registration
    """
    if not registration.onfido_document_ids:
        raise Exception('No documents uploaded')
    
    check_response = api.check.create({
        'applicant_id': registration.onfido_applicant_id,
        'report_names': [
            'document',
        ],
        'document_ids': registration.onfido_document_ids,
        'applicant_provides_data': False,
    })

    registration.onfido_check_response = check_response
    registration.kyc_status = 'WAITING_FOR_CHECK_RESPONSE'
    registration.save()

    return registration

def update_check_status(registration):
    """
    Update the status of a check.
    
    Args:
        registration: The registration to update
        
    Returns:
        Registration: The updated registration
    """
    if not registration.onfido_check_response:
        raise Exception('No check data')

    check = api.check.find(
        registration.onfido_check_response['id']
    )

    if check:
        registration.onfido_check_response = check

        done = False

        if check['status'] == 'complete':
            registration.kyc_status = 'COMPLETE'
            registration.complete = True
            done = True
        elif check['status'] == 'reopened':
            registration.kyc_status = 'FAILED'
            done = True

        if done:
            reports = api.report.all(check_id=check['id'])['reports']
            registration.onfido_reports = reports

            for r in reports:
                if r['name'] == 'document':
                    new_first_name = r['properties'].get('first_name')
                    if new_first_name:
                        registration.first_name = new_first_name
                    
                    new_last_name = r['properties'].get('last_name')
                    if new_last_name:
                        registration.last_name = new_last_name
                    
                    new_bday = r['properties'].get('date_of_birth')
                    if new_bday:
                        registration.birthday = new_bday
                    
        registration.save()

    return registration

    