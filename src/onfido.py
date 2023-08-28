import onfido
import os
from src.models.registration import Registration, Callback
import datetime
from onfido.regions import Region

api = onfido.Api(os.getenv('ONFIDO_API_KEY'), region = Region.US)

def generate_sdk_token(applicant_id: str):
    response = api.sdk_token.generate({
        'applicant_id': applicant_id,
        # 'referrer': 'http://localhost:5502/register/*'
    })

    return response['token']



def run_verification_request():
    registration = Registration(
        started_at=datetime.datetime.utcnow()
    )

    registration.save()
    applicant_details = {
    'first_name': 'ApuestaPR',
    'last_name': 'Customer',
    'dob': '1984-01-01',
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
            done = True

            
        elif check['status'] == 'reopened':
            registration.kyc_status == 'FAILED'
            done = True

        if done:
            # Get the reports
            reports = api.report.all(check_id=check['id'])['reports']
            print('REPORTs', reports)
            registration.onfido_reports = reports

            # Update the user information from the reports
            for r in reports:
                print(r)

                if r['name'] == 'document':

                    registration.first_name = r['properties']['first_name']
                    registration.last_name = r['properties']['last_name']
                    registration.birthday = r['properties']['date_of_birth']
        

        registration.save()

    return registration

    