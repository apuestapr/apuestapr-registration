from src.models.mongo import MongoModel
from pydantic import BaseModel
import datetime
import typing


class Callback(BaseModel):
    timestamp: datetime.datetime
    body: typing.Optional[typing.Any] = None


class Registration(MongoModel):
    started_at: datetime.datetime = None
    callbacks: typing.List[Callback] = []
    kyc_status: str = 'PENDING'
    first_name: str = ''
    last_name: str = ''
    birthday: typing.Optional[str] = ''
    gender: str = ''
    email: str = ''
    phone_number: str = ''
    loyalty_card_number: str = ''
    complete: bool = False
    kyc_override: str = ''
    preferred_language: str = 'es'
    referral_code: str = ''
    registered_by: str = ''

    agree_to_terms: bool = False

    address_1: str = ''
    address_2: str = ''
    city: str = ''
    state_province: str = ''
    postal_code: str = ''
    country: str = ''

    # Tracks which KYC provider was used for this registration
    kyc_provider: str = ''

    # Onfido specific fields
    onfido_applicant_id: str = ''
    onfido_check_response: typing.Any = None
    onfido_document_ids: typing.Optional[typing.List[str]] = None
    onfido_reports: typing.Any = None

    # Shufti Pro specific fields
    shufti_reference: str = ''
    shufti_callback_payload: typing.Any = None

    # Didit specific fields
    didit_session_id: str = ''
    didit_callback_payload: typing.Any = None

    # Whitehat fields
    whitehat_user_id: str = ''
    whitehat_kyc_approved: bool = False
    whitehat_playerid: str = ''

    def safe_serialize(self):
        data = {
            '_id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'kyc_status': self.kyc_status,
            'kyc_provider': self.kyc_provider,
            'email': self.email,
            'phone_number': self.phone_number,
            'preferred_language': self.preferred_language,
            'birthday': self.birthday,
            'account_id': self.whitehat_playerid,
            'loyalty_card_number': self.loyalty_card_number,
            'referral_code': self.referral_code,
            'whitehat_user_id': self.whitehat_user_id
        }
        
        # Add provider-specific fields based on which provider was used
        if self.kyc_provider == 'onfido' or not self.kyc_provider:
            data['onfido_applicant_id'] = self.onfido_applicant_id
        elif self.kyc_provider == 'shufti':
            data['shufti_reference'] = self.shufti_reference
        elif self.kyc_provider == 'didit':
            data['didit_session_id'] = self.didit_session_id
            
        return data

# XXX todo: login, populate referral code from the user.
# XXX todo: update users with diff card number?

def serialize_documents(documents):
    serialized_docs = []
    for document in documents:
        registration = Registration(**document)
        serialized_docs.append(registration.safe_serialize())
    return serialized_docs
