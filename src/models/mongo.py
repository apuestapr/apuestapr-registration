import os
from typing import List, Union, Optional, Set
from uuid import UUID
from pymongo import MongoClient, ASCENDING
from pydantic import BaseModel, Field
from bson.objectid import ObjectId
from datetime import datetime
from pymongo.server_api import ServerApi


client = MongoClient(os.getenv('MONGO_CONNECTION_STRING'), server_api=ServerApi('1'))

# This will not recreate it if it already exists; just ensures that it's unique
client['registrations']['registration'].create_index('loyalty_card_number', sparse=True)

def db():
    return client['registrations']
    

class IndexField(BaseModel):
    field: str
    sort: int = ASCENDING
    

class ModelIndex(BaseModel):
    fields: List[IndexField]
    unique: bool = False


class MongoModel(BaseModel):
    id: ObjectId = Field(alias='_id', default=None)
    last_updated: datetime = None
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        indexes = []
    
    @classmethod
    def collection_name(klass):
        if hasattr(klass.Config, 'collection_name'):
            return klass.Config.collection_name
        return str(klass.__name__).lower()

    @classmethod
    def collection(klass):
        return db()[klass.collection_name()]
    

    @classmethod
    def ensure_indexes(klass):
        if not hasattr(klass.Config, 'indexes'):
            return 
        
        for index in klass.Config.indexes:
            if not isinstance(index, ModelIndex):
                raise Exception(f"Unrecognized index class {index}")
    
            klass.collection().create_index(
                [(f.field, f.sort) for f in index.fields],
                unique=index.unique
            )
    

    @classmethod
    def find_by_id(klass, id: Union[str, ObjectId]):
        if type(id) == str:
            id = ObjectId(id)
        
        return klass.find_one({
            '_id': id
        })

    @classmethod
    def find(klass, filter=None, skip: int = None, limit: int = None, sort: str = None):
        results = klass.collection().find(filter)
        if skip:
            results = results.skip(skip)
        if limit:
            results = results.limit(limit)
        if sort:
            if sort.startswith('-'):
                results = results.sort(sort[1:], -1)
            else:
                results = results.sort(sort)

        return [klass(**r) for r in results]
    

    @classmethod
    def find_one(klass, filter=None):
        result = klass.collection().find_one(filter)
        if not result:
            return None
        return klass(**result)

    @classmethod
    def count(klass, filter=None):

        return klass.collection().count_documents(filter or {})

    @classmethod
    def delete_many(klass, filter):
        if not filter:
            raise Exception('Set a filter to delete multiple')
        return klass.collection().delete_many(filter)


    def save(self, include: Optional[Set[str]] = None, exclude: Optional[Set[str]] = None):
        self.last_updated = datetime.utcnow()
        data = self.dict()

        if self.id is None:
            new_id = self.collection().insert_one(data).inserted_id
            self.id = new_id
        else:
            filter = {
                '_id': self.id
            }
            self.collection().update_one(filter, {
                '$set': data,
            })

    def delete(self):
        return self.collection().delete_one({
            '_id': self.id,
        })

    


