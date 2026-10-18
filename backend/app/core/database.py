import logging
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Mock MongoDB Implementation for local/offline run ---
class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = {}
        self._counter = 1

    async def insert_one(self, document):
        if "_id" not in document:
            document["_id"] = f"{self.name}_{self._counter}"
            self._counter += 1
        self.data[document["_id"]] = document
        return type('obj', (object,), {'inserted_id': document["_id"], 'acknowledged': True})()

    async def find_one(self, filter):
        for doc in self.data.values():
            match = True
            for k, v in filter.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                import copy
                return copy.deepcopy(doc)
        return None

    def find(self, filter=None):
        filter = filter or {}
        results = []
        for doc in self.data.values():
            match = True
            for k, v in filter.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                import copy
                results.append(copy.deepcopy(doc))
        
        class Cursor:
            def __init__(self, data_list):
                self.data_list = data_list
            def __aiter__(self):
                return self
            async def __anext__(self):
                if not self.data_list:
                    raise StopAsyncIteration
                return self.data_list.pop(0)
            async def to_list(self, length=None):
                if length:
                    return self.data_list[:length]
                return self.data_list
            def sort(self, key_or_list, direction=None):
                # Simulated sorting by timestamp or name
                try:
                    # simplistic sorting by timestamp if it exists, descending by default
                    self.data_list.sort(key=lambda x: x.get("timestamp" if "timestamp" in x else "_id"), reverse=True)
                except Exception:
                    pass
                return self
        return Cursor(results)

    async def update_one(self, filter, update):
        doc = await self.find_one(filter)
        if not doc:
            return type('obj', (object,), {'modified_count': 0, 'matched_count': 0})()
        
        # Simple implementation of $set
        if "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v
        else:
            for k, v in update.items():
                doc[k] = v
        self.data[doc["_id"]] = doc
        return type('obj', (object,), {'modified_count': 1, 'matched_count': 1})()

    async def delete_one(self, filter):
        doc = await self.find_one(filter)
        if doc and doc["_id"] in self.data:
            del self.data[doc["_id"]]
            return type('obj', (object,), {'deleted_count': 1})()
        return type('obj', (object,), {'deleted_count': 0})()

class MockDatabase:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

class MockMongoClient:
    def __init__(self):
        self.db = MockDatabase()
    def get_database(self, name):
        return self.db
    def __getitem__(self, name):
        return self.db

# --- Database Clients initialization ---
db_client = None
db = None

try:
    # Try connecting to actual MongoDB with a short timeout (1 second) using a sync client to check connectivity
    from pymongo import MongoClient
    sync_client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=1000)
    sync_client.admin.command('ping')
    
    # If successful, initialize AsyncIOMotorClient
    db_client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
    db = db_client[settings.DATABASE_NAME]
    logger.info("Successfully configured MongoDB connection client.")
except Exception as e:
    logger.warning(f"Failed to connect to actual MongoDB ({e}). Falling back to In-Memory Database.")
    db_client = MockMongoClient()
    db = db_client.get_database(settings.DATABASE_NAME)


def get_db():
    return db

