from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.repositories.user_repo import UserRepository
from app.core.security import get_current_user_payload, RoleChecker
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["System Administration"])

# Secure router under ADMIN permissions only
admin_check = RoleChecker(["admin"])

def get_user_repository(db = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

@router.get("/audit-logs", dependencies=[Depends(admin_check)])
async def get_audit_logs(
    db = Depends(get_db)
) -> List[Dict[str, Any]]:
    # Get all logs, sorted by timestamp descending
    cursor = db["audit_logs"].find()
    logs = await cursor.to_list(length=100)
    try:
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    except Exception:
        pass
    
    # Map _id object to string for JSON serialization compatibility
    serialized_logs = []
    for log in logs:
        log["_id"] = str(log["_id"])
        if "timestamp" in log and isinstance(log["timestamp"], datetime):
            log["timestamp"] = log["timestamp"].isoformat()
        serialized_logs.append(log)
    return serialized_logs

@router.put("/rbac/{user_id}", dependencies=[Depends(admin_check)])
async def update_user_role(
    user_id: str,
    payload_data: Dict[str, str], # {"role": "coder"}
    user_repo: UserRepository = Depends(get_user_repository),
    db = Depends(get_db),
    admin_user: dict = Depends(get_current_user_payload)
):
    target_role = payload_data.get("role")
    if target_role not in ["admin", "doctor", "coder", "auditor"]:
        raise HTTPException(status_code=400, detail="Invalid target role specification")
        
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")
        
    updated = await user_repo.update(user_id, {"role": target_role})
    
    # Audit log
    audit_data = {
        "user_id": admin_user.get("sub", "admin"),
        "user_name": admin_user.get("name", "Administrator"),
        "role": "admin",
        "action": "RBAC_USER_ROLE_MODIFIED",
        "resource_id": user_id,
        "details": f"Changed role of user {user['email']} from {user['role']} to {target_role}",
        "ip_address": "127.0.0.1",
        "timestamp": datetime.utcnow()
    }
    await db["audit_logs"].insert_one(audit_data)
    
    return {"message": "User role updated successfully", "email": user["email"], "new_role": target_role}
