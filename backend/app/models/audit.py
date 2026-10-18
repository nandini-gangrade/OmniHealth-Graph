from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class AuditLogCreate(BaseModel):
    user_id: str
    user_name: str
    role: str
    action: str
    resource_id: Optional[str] = None
    details: str
    ip_address: Optional[str] = "127.0.0.1"

class AuditLog(AuditLogCreate):
    id: str = Field(alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
