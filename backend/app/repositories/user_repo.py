from app.repositories.base import BaseRepository
from app.core.security import get_password_hash
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository):
    def __init__(self, db: Any):
        super().__init__(db, "users")

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"email": email})

    async def seed_default_users(self):
        # Check if users already exist
        existing = await self.list(limit=1)
        if not existing:
            logger.info("No users found in database. Seeding default roles...")
            default_users = [
                {
                    "_id": "usr_doctor_1",
                    "email": "doctor@hospital.com",
                    "full_name": "Dr. Sarah Elizabeth, MD",
                    "role": "doctor",
                    "hashed_password": get_password_hash("doctor123"),
                    "is_active": True,
                    "consent_given": True,
                    "created_at": datetime.utcnow()
                },
                {
                    "_id": "usr_coder_1",
                    "email": "coder@hospital.com",
                    "full_name": "John Miller, CPC (Medical Coder)",
                    "role": "coder",
                    "hashed_password": get_password_hash("coder123"),
                    "is_active": True,
                    "consent_given": True,
                    "created_at": datetime.utcnow()
                },
                {
                    "_id": "usr_auditor_1",
                    "email": "auditor@hospital.com",
                    "full_name": "Alice Cooper, CHC (Compliance Auditor)",
                    "role": "auditor",
                    "hashed_password": get_password_hash("auditor123"),
                    "is_active": True,
                    "consent_given": True,
                    "created_at": datetime.utcnow()
                },
                {
                    "_id": "usr_admin_1",
                    "email": "admin@hospital.com",
                    "full_name": "System Administrator",
                    "role": "admin",
                    "hashed_password": get_password_hash("admin123"),
                    "is_active": True,
                    "consent_given": True,
                    "created_at": datetime.utcnow()
                }
            ]
            for user in default_users:
                await self.collection.insert_one(user)
            logger.info("Successfully seeded default accounts.")
