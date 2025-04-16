import onfido
import os
import datetime
from onfido.regions import Region
from src.models.registration import Registration

# Initialize the Onfido API client
api = onfido.Api(os.getenv('ONFIDO_API_KEY'), region=Region.US)

def generate_sdk_token(applicant_id: str) -> str:
    """Generate an SDK token for the Onfido frontend library"""
    response = api.sdk_token.generate({
        'applicant_id': applicant_id,
    })
    return response['token']

def create_applicant(registration: Registration) -> dict:
    """Create an applicant in Onfido's system"""
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
    
    # Call the API to create an applicant
    return api.applicant.create(applicant_details)

def create_check(applicant_id: str, document_ids: list) -> dict:
    """Create a verification check for the applicant"""
    if not document_ids:
        raise Exception('No documents uploaded')
    
    return api.check.create({
        'applicant_id': applicant_id,
        'report_names': [
            'document',
        ],
        'document_ids': document_ids,
        'applicant_provides_data': False,
    })

def get_check_status(check_id: str) -> dict:
    """Get the current status of a verification check"""
    return api.check.find(check_id)

def get_reports(check_id: str) -> list:
    """Get the reports associated with a check"""
    return api.report.all(check_id=check_id)['reports']