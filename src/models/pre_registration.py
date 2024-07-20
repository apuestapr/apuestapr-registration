from src.models.mongo import MongoModel
from pydantic import BaseModel, Field
import datetime
import typing
from bson import ObjectId

class Callback(BaseModel):
    timestamp: datetime.datetime
    body: typing.Any

class PreRegistration(MongoModel):
    class Config:
        collection_name = 'pre-registration'

    createdAt: datetime = Field(default_factory=datetime.datetime.now)
    first_name: str = ''
    last_name: str = ''
    address_1: str = ''
    address_2: str = ''
    city: str = ''
    postal_code: str = ''
    country: str = ''
    state_province: str = ''
    birthdate: str = ''
    phone_number: str = ''
    email: str = ''

    def safe_serialize(self):
        return {
            '_id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'address_1': self.address_1,
            'address_2': self.address_2,
            'city': self.city,
            'state_province': self.state_province,
            'country': self.country,
            'postal_code': self.postal_code,
            'phone_number': self.phone_number,
            'birthdate': self.birthdate,
            'createdAt': self.createdAt.isoformat(),
            'createdAt_short': self.createdAt.strftime('%m/%d/%Y') if self.createdAt else None,
        }

def serialize_documents(documents):
    serialized_docs = []
    for document in documents:
        pre_registration = PreRegistration(**document)
        serialized_docs.append(pre_registration.safe_serialize())
    return serialized_docs