from typing import Generic, TypeVar, List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

T = TypeVar("T")

class BaseRepository:
    def __init__(self, db: Any, collection_name: str):
        self.db = db
        self.collection = db[collection_name]

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": id})

    async def list(self, filter: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        filter = filter or {}
        cursor = self.collection.find(filter)
        return await cursor.to_list(length=limit)

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if "_id" not in data:
            data["_id"] = str(uuid.uuid4())
        await self.collection.insert_one(data)
        return data

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        await self.collection.update_one({"_id": id}, {"$set": data})
        return await self.get(id)

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"_id": id})
        return getattr(result, "deleted_count", 0) > 0
