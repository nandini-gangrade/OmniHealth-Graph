from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_db
from app.repositories.user_repo import UserRepository
from app.models.auth import UserCreate, UserResponse, Token
from app.core.security import verify_password, create_access_token, get_password_hash
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_user_repository(db = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository)
):
    # Retrieve user by email
    user = await user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")

    # Generate JWT
    access_token = create_access_token(
        subject=user["email"],
        expires_delta=None
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user["role"],
        full_name=user["full_name"]
    )

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository)
):
    # Check if user already exists
    existing = await user_repo.get_by_email(user_in.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists in the system."
        )
    
    # Construct user DB object
    user_dict = user_in.model_dump()
    password = user_dict.pop("password")
    user_dict["hashed_password"] = get_password_hash(password)
    
    created = await user_repo.create(user_dict)
    
    # Map _id string
    return UserResponse(
        id=created["_id"],
        email=created["email"],
        full_name=created["full_name"],
        role=created["role"],
        is_active=created["is_active"],
        consent_given=created["consent_given"]
    )
