from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models.user import UserCreate, UserResponse, Token, TokenData
from utils.auth import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from database import get_db
from datetime import timedelta, datetime
from config import settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    token_data = decode_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_db()
    user = await db.users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user["username"], "role": user["role"]}, expires_delta=refresh_token_expires
    )
    
    # Include user data in the response
    created_at = user.get("created_at", datetime.utcnow())
    
    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": user["role"],
            "is_active": user.get("is_active", True),
            "created_at": created_at.isoformat() if isinstance(created_at, datetime) else created_at
        }
    }
    
    return response_data

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    db = get_db()
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict["hashed_password"] = hashed_password
    user_dict.pop("password")
    
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    # Convert MongoDB ObjectId to string and ensure all required fields are present
    created_user["id"] = str(created_user["_id"])
    created_user.pop("_id")
    created_user["created_at"] = created_user.get("created_at", datetime.utcnow())
    
    return UserResponse(**created_user)

@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(current_user: TokenData = Depends(get_current_user)):
    db = get_db()
    user = await db.users.find_one({"username": current_user.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

@router.post("/token/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    token_data = decode_token(refresh_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": token_data.username, "role": token_data.role}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }