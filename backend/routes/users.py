from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from models.user import UserResponse, UserCreate, TokenData
from utils.auth import decode_token
from database import get_db

# Import get_current_user locally to avoid circular import
from routes.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 100, role: str = None):
    db = get_db()
    query = {}
    if role:
        query["role"] = role
    users = []
    async for user in db.users.find(query).skip(skip).limit(limit):
        # Convert MongoDB _id to id and ensure all required fields are present
        user_dict = dict(user)
        user_dict["id"] = str(user_dict.pop("_id"))
        # Ensure created_at is present
        if "created_at" not in user_dict:
            user_dict["created_at"] = datetime.utcnow()
        users.append(UserResponse(**user_dict))
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    db = get_db()
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Convert MongoDB _id to id and ensure all required fields are present
    user_dict = dict(user)
    user_dict["id"] = str(user_dict.pop("_id"))
    # Ensure created_at is present
    if "created_at" not in user_dict:
        user_dict["created_at"] = datetime.utcnow()
    return UserResponse(**user_dict)

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: TokenData = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create users")
    
    db = get_db()
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    from utils.auth import get_password_hash
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict["hashed_password"] = hashed_password
    user_dict.pop("password")
    
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    # Convert MongoDB _id to id and ensure all required fields are present
    created_user_dict = dict(created_user)
    created_user_dict["id"] = str(created_user_dict.pop("_id"))
    # Ensure created_at is present
    if "created_at" not in created_user_dict:
        created_user_dict["created_at"] = datetime.utcnow()
    return UserResponse(**created_user_dict)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: dict, current_user: TokenData = Depends(get_current_user)):
    db = get_db()
    existing_user = await db.users.find_one({"_id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if current_user.role != "admin" and current_user.username != existing_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    update_data = {k: v for k, v in user_data.items() if k != "id"}
    await db.users.update_one({"_id": user_id}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"_id": user_id})
    # Convert MongoDB _id to id and ensure all required fields are present
    updated_user_dict = dict(updated_user)
    updated_user_dict["id"] = str(updated_user_dict.pop("_id"))
    # Ensure created_at is present
    if "created_at" not in updated_user_dict:
        updated_user_dict["created_at"] = datetime.utcnow()
    return UserResponse(**updated_user_dict)

@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(user_id: str, current_user: TokenData = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")
    
    db = get_db()
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.delete_one({"_id": user_id})
    # Convert MongoDB _id to id and ensure all required fields are present before returning
    user_dict = dict(user)
    user_dict["id"] = str(user_dict.pop("_id"))
    # Ensure created_at is present
    if "created_at" not in user_dict:
        user_dict["created_at"] = datetime.utcnow()
    return UserResponse(**user_dict)

@router.post("/{user_id}/activate")
async def activate_user(user_id: str, current_user: TokenData = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can activate users")
    
    db = get_db()
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one({"_id": user_id}, {"$set": {"is_active": True}})
    return {"message": "User activated successfully"}

@router.get("/count/stats")
async def get_user_stats():
    db = get_db()
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    admin_users = await db.users.count_documents({"role": "admin"})
    doctor_users = await db.users.count_documents({"role": "doctor"})
    
    return {
        "total": total_users,
        "active": active_users,
        "admins": admin_users,
        "doctors": doctor_users,
    }