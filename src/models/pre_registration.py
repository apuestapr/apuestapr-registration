from src.models.mongo import MongoModel
from pydantic import BaseModel
import datetime
import typing

class Callback(BaseModel):
    timestamp: datetime.datetime
    body: typing.Any

class PreRegistration(MongoModel):
    class Config:
        collection_name = 'pre-registration'

    # started_at: datetime.datetime
    # callbacks: typing.List[Callback] = []
    first_name: str = ''
    last_name: str = ''

    def safe_serialize(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
        }

# XXX todo: login, populate referral code from the user.
# XXX todo: update users with diff card number?
