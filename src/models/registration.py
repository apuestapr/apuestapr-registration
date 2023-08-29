from src.models.mongo import MongoModel
from pydantic import BaseModel
import datetime
import typing



class Callback(BaseModel):
    timestamp: datetime.datetime
    body: typing.Any

class Registration(MongoModel):
    started_at: datetime.datetime
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

    onfido_applicant_id: str = ''

    onfido_check_response: typing.Any = None
    onfido_document_ids: typing.Optional[typing.List[str]] = None
    onfido_reports: typing.Any = None



# XXX todo: login, populate referral code from the user.
# XXX todo: update users with diff card number?