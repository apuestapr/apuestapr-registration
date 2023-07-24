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
    kyc_status: str = ''
    first_name: str = ''
    last_name: str = ''
    birthday: typing.Optional[str] = ''
    gender: str = ''
    email: str = ''
    phone_number: str = ''
    loyalty_card_number: str = ''
    complete: bool = False
    kyc_override: str = ''



