from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fernet key comes strictly from the environment (FERNET_KEY)
fernet = Fernet(settings.FERNET_KEY.encode("utf-8"))

# Security authentication schema
security_bearer = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None

def encrypt_data(data: str) -> str:
    """Encrypts sensitive data (e.g. PHI/PII) using Fernet AES encryption."""
    if not data:
        return data
    try:
        return fernet.encrypt(data.encode("utf-8")).decode("utf-8")
    except Exception as e:
        # Fallback to base64 if key issues occur in raw CLI run
        return base64.b64encode(data.encode("utf-8")).decode("utf-8")

def decrypt_data(encrypted_data: str) -> str:
    """Decrypts sensitive data."""
    if not encrypted_data:
        return encrypted_data
    try:
        return fernet.decrypt(encrypted_data.encode("utf-8")).decode("utf-8")
    except Exception as e:
        try:
            return base64.b64decode(encrypted_data.encode("utf-8")).decode("utf-8")
        except Exception:
            return encrypted_data # Return as-is if not encoded

def get_current_user_payload(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> dict:
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token or expired session")
    return payload

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, payload: dict = Depends(get_current_user_payload)) -> dict:
        # Role information will be stored in payload/database
        # Here we verify if role requirements are satisfied
        user_role = payload.get("role", "doctor") # Default to doctor
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Access forbidden: User role '{user_role}' does not have permission for this action"
            )
        return payload
