"""
Authentication API Routes for CarthaNeuro
Handles user registration, login, logout, and profile management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional

from src.auth.auth_service import auth_service, UserRegister, UserLogin, Token
from src.auth.auth_middleware import (
    get_current_user, 
    get_current_user_optional, 
    get_user_id_from_token,
    guest_only,
    get_user_context
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Create router
auth_router = APIRouter()

# Request/Response Models
class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    tokens: Optional[dict] = None

class LogoutResponse(BaseModel):
    success: bool
    message: str

@auth_router.post("/register", response_model=AuthResponse)
async def register_user(
    user_data: UserRegister,
    user_context: dict = Depends(get_user_context)
):
    """
    Register a new user account
    """
    try:
        result = await auth_service.register_user(user_data)
        
        logger.info(f"User registered successfully: {user_data.email}")
        
        return AuthResponse(
            success=True,
            message="User registered successfully",
            user={
                "user_id": result["user_id"],
                "username": user_data.username,
                "email": user_data.email
            },
            tokens=result["tokens"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@auth_router.post("/login", response_model=AuthResponse)
async def login_user(
    login_data: UserLogin,
    user_context: dict = Depends(get_user_context)
):
    """
    Login user and return JWT tokens
    """
    try:
        result = await auth_service.login_user(login_data)
        
        return AuthResponse(
            success=True,
            message="Login successful",
            user=result["user"].dict(),
            tokens=result["tokens"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@auth_router.post("/refresh", response_model=AuthResponse)
async def refresh_access_token(
    token_data: RefreshTokenRequest,
    user_context: dict = Depends(get_user_context)
):
    """
    Refresh access token using refresh token
    """
    try:
        result = await auth_service.refresh_token(token_data.refresh_token)
        
        return AuthResponse(
            success=True,
            message="Token refreshed successfully",
            tokens=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@auth_router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    user_id: str = Depends(get_user_id_from_token),
    user_context: dict = Depends(get_user_context)
):
    """
    Logout user (client-side token removal)
    """
    try:
        logger.info(f"User logged out: {user_id}")
        
        return LogoutResponse(
            success=True,
            message="Logout successful"
        )
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@auth_router.get("/me", response_model=AuthResponse)
async def get_current_user_profile(
    current_user = Depends(get_current_user),
    user_context: dict = Depends(get_user_context)
):
    """
    Get current user profile information
    """
    try:
        return AuthResponse(
            success=True,
            message="User profile retrieved",
            user=current_user.dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to get user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@auth_router.put("/me", response_model=AuthResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user = Depends(get_current_user),
    user_context: dict = Depends(get_user_context)
):
    """
    Update current user profile
    """
    try:
        from src.database.mongodb_service import get_db_operations
        
        db_ops = get_db_operations()
        
        # Prepare update data
        update_data = {}
        if profile_data.first_name is not None:
            update_data["first_name"] = profile_data.first_name
        if profile_data.last_name is not None:
            update_data["last_name"] = profile_data.last_name
        
        if not update_data:
            return AuthResponse(
                success=True,
                message="No changes to update",
                user=current_user.dict()
            )
        
        # Update user
        success = await db_ops.update_user(current_user.user_id, update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        # Get updated user
        updated_user = await auth_service.get_user_by_id(current_user.user_id)
        
        logger.info(f"User profile updated: {current_user.user_id}")
        
        return AuthResponse(
            success=True,
            message="Profile updated successfully",
            user=updated_user.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@auth_router.post("/change-password", response_model=AuthResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    user_id: str = Depends(get_user_id_from_token),
    user_context: dict = Depends(get_user_context)
):
    """
    Change user password
    """
    try:
        result = await auth_service.change_password(
            user_id, 
            password_data.old_password, 
            password_data.new_password
        )
        
        logger.info(f"Password changed successfully for user: {user_id}")
        
        return AuthResponse(
            success=True,
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@auth_router.post("/verify-email/{user_id}")
async def verify_user_email(
    user_id: str,
    current_user = Depends(get_current_user),
    user_context: dict = Depends(get_user_context)
):
    """
    Verify user email address
    """
    try:
        # Only allow users to verify their own email
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot verify another user's email"
            )
        
        success = await auth_service.verify_user_email(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email verification failed"
            )
        
        logger.info(f"Email verified for user: {user_id}")
        
        return {
            "success": True,
            "message": "Email verified successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )

@auth_router.get("/check-email")
async def check_email_exists(
    email: EmailStr,
    user_context: dict = Depends(get_user_context)
):
    """
    Check if email already exists (for registration form validation)
    """
    try:
        from src.database.mongodb_service import get_db_operations
        
        db_ops = get_db_operations()
        existing_user = await db_ops.get_user_by_email(email)
        
        return {
            "success": True,
            "email_exists": existing_user is not None
        }
        
    except Exception as e:
        logger.error(f"Email check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email check failed"
        )

@auth_router.get("/check-username")
async def check_username_exists(
    username: str,
    user_context: dict = Depends(get_user_context)
):
    """
    Check if username already exists (for registration form validation)
    """
    try:
        from src.database.mongodb_service import get_db_operations
        
        db_ops = get_db_operations()
        existing_user = await db_ops.users.find_one({"username": username})
        
        return {
            "success": True,
            "username_exists": existing_user is not None
        }
        
    except Exception as e:
        logger.error(f"Username check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Username check failed"
        )

@auth_router.get("/status")
async def auth_status(
    current_user: Optional[dict] = Depends(get_current_user_optional),
    user_context: dict = Depends(get_user_context)
):
    """
    Get authentication status (useful for frontend)
    """
    try:
        return {
            "success": True,
            "authenticated": current_user is not None,
            "user": current_user.dict() if current_user else None
        }
        
    except Exception as e:
        logger.error(f"Auth status check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Status check failed"
        )

# Export router
__all__ = ["auth_router"]