"""
Authentication Middleware and Dependencies for FastAPI
Provides JWT token validation and user authentication
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.base import SecurityBase
from typing import Optional
from urllib.parse import urlparse, parse_qs

from src.auth.auth_service import auth_service, TokenData, UserResponse
from src.database.mongodb_service import get_db_operations
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Security scheme for JWT bearer tokens
security = HTTPBearer(auto_error=False)

class AuthMiddleware:
    """Authentication middleware for FastAPI endpoints"""
    
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> UserResponse:
        """
        Dependency to get current authenticated user
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            # Verify token and get user ID
            token_data = auth_service.verify_token(credentials.credentials)
            
            if not token_data.user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Get user from database
            user = await auth_service.get_user_by_id(token_data.user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is disabled",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    async def get_current_user_optional(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Optional[UserResponse]:
        """
        Optional authentication dependency - returns None if not authenticated
        """
        if not credentials:
            return None
        
        try:
            token_data = auth_service.verify_token(credentials.credentials)
            if not token_data.user_id:
                return None
            
            user = await auth_service.get_user_by_id(token_data.user_id)
            if user and user.is_active:
                return user
            return None
            
        except Exception as e:
            logger.warning(f"Optional authentication failed: {str(e)}")
            return None
    
    @staticmethod
    async def get_current_active_user(
        current_user: UserResponse
    ) -> UserResponse:
        """
        Dependency to ensure user is active
        """
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        return current_user
    
    @staticmethod
    async def get_admin_user(
        current_user: UserResponse
    ) -> UserResponse:
        """
        Dependency to ensure user is an admin
        """
        if current_user.role != "admin" and current_user.role != "system_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return current_user
    
    @staticmethod
    async def get_user_id_from_token(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> str:
        """
        Dependency to get user ID from token
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        try:
            token_data = auth_service.verify_token(credentials.credentials)
            if not token_data.user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return token_data.user_id
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    @staticmethod
    async def get_user_id_from_token_with_query(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> str:
        """
        Dependency to get user ID from token - supports both header and query parameter
        """
        token = None
        
        # First try header
        if credentials:
            token = credentials.credentials
        
        # If no header token, try query parameter
        if not token:
            try:
                # Parse query parameters
                query_params = request.query_params
                token = query_params.get('token')
                
                # Also try Authorization header from query string for SSE
                if not token:
                    auth_header = query_params.get('authorization')
                    if auth_header and auth_header.startswith('Bearer '):
                        token = auth_header.replace('Bearer ', '')
            except Exception as e:
                logger.warning(f"Failed to parse query parameters: {str(e)}")
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required - provide token in header or query parameter"
            )
        
        try:
            token_data = auth_service.verify_token(token)
            if not token_data.user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return token_data.user_id
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

# Convenience dependency functions that properly chain dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    """Get current authenticated user"""
    return await AuthMiddleware.get_current_user(credentials)

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[UserResponse]:
    """Optional authentication dependency"""
    return await AuthMiddleware.get_current_user_optional(credentials)

async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Dependency to ensure user is active"""
    return await AuthMiddleware.get_current_active_user(current_user)

async def get_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Dependency to ensure user is an admin"""
    return await AuthMiddleware.get_admin_user(current_user)

async def get_user_id_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get user ID from token"""
    return await AuthMiddleware.get_user_id_from_token(credentials)

async def get_user_id_from_token_with_query(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get user ID from token (supports query parameters for SSE)"""
    return await AuthMiddleware.get_user_id_from_token_with_query(request, credentials)

# Role-based access control decorator
def require_role(role: str):
    """
    Decorator to require specific role for endpoint access
    """
    def role_checker(current_user: UserResponse = Depends(get_current_user)):
        if current_user.role != role and current_user.role not in ["admin", "system_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{role.capitalize()} access required"
            )
        return current_user
    return role_checker

# Permission-based access control
def require_permissions(permissions: list):
    """
    Decorator to require specific permissions
    """
    def permission_checker(current_user: UserResponse = Depends(get_current_user)):
        # This would implement fine-grained permission checking
        # For now, role-based access is sufficient
        allowed_roles = ["admin", "system_admin"]
        if current_user.role not in allowed_roles:
            # Check specific permissions against user preferences or role
            if "admin" in permissions and current_user.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin permission required"
                )
        return current_user
    return permission_checker

# Auth decorator for protected endpoints
def require_auth(user: UserResponse = Depends(get_current_user)):
    """
    Simple authentication decorator
    """
    return user

# Guest-only decorator (for registration/login pages)
def guest_only(user: Optional[UserResponse] = Depends(get_current_user_optional)):
    """
    Decorator for endpoints that should only be accessible to guests
    """
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already authenticated"
        )
    return None

# Token validation helper
async def validate_token(token: str) -> bool:
    """
    Helper function to validate a token
    """
    try:
        token_data = auth_service.verify_token(token)
        return token_data.user_id is not None
    except Exception:
        return False

# Get user context
async def get_user_context(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get user context for logging and audit purposes
    """
    context = {
        "user_id": None,
        "username": None,
        "email": None,
        "role": None,
        "authenticated": False
    }
    
    if credentials:
        try:
            token_data = auth_service.verify_token(credentials.credentials)
            user = await auth_service.get_user_by_id(token_data.user_id)
            if user:
                context.update({
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "authenticated": True
                })
        except Exception as e:
            logger.warning(f"Failed to get user context: {str(e)}")
    
    return context

# Export auth dependencies
__all__ = [
    "get_current_user",
    "get_current_user_optional", 
    "get_current_active_user",
    "get_admin_user",
    "get_user_id_from_token",
    "get_user_id_from_token_with_query",
    "require_role",
    "require_permissions",
    "require_auth",
    "guest_only",
    "validate_token",
    "get_user_context"
]