from app.repositories.base import BaseRepository
from typing import List, Dict, Any

class SessionRepository(BaseRepository):
    def __init__(self, db: Any):
        super().__init__(db, "sessions")

    async def get_by_doctor(self, doctor_id: str) -> List[Dict[str, Any]]:
        return await self.list({"doctor_id": doctor_id})

    async def get_all_sessions_sorted(self) -> List[Dict[str, Any]]:
        # The base list returns cursor, but we can do list and let base handle it
        # Under the hood we sort by created_at descending
        results = await self.list()
        try:
            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        except Exception:
            pass
        return results
