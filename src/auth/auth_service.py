"""
Authentication Service for CarthaNeuro
Handles user registration, login, password hashing, and JWT token management
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import BaseModel

from src.config.settings import settings
from src.database.mongodb_service import get_db_operations, UserDocument
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class AuthService:
    """Authentication service with JWT and password hashing"""
    
    def __init__(self):
        self._db_ops = None
    
    @property
    def db_ops(self):
        if self._db_ops is None:
            self._db_ops = get_db_operations()
        return self._db_ops
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash with multiple format support"""
        try:
            # Handle different hash formats
            if hashed_password.startswith("pbkdf2_sha256$"):
                # Verify pbkdf2_sha256 fallback hash
                import hashlib
                try:
                    parts = hashed_password.split("$")
                    if len(parts) != 4:
                        logger.error(f"Invalid pbkdf2 hash format: {hashed_password[:20]}...")
                        return False
                    iterations = int(parts[1])
                    salt = parts[2]
                    stored_hash = parts[3]
                    
                    computed_hash = hashlib.pbkdf2_hmac(
                        'sha256', 
                        plain_password.encode('utf-8'), 
                        salt.encode('utf-8'), 
                        iterations
                    ).hex()
                    
                    result = computed_hash == stored_hash
                    logger.debug(f"PBKDF2 verification {'succeeded' if result else 'failed'}")
                    return result
                except Exception as e:
                    logger.error(f"PBKDF2 verification failed: {str(e)}")
                    return False
                    
            elif hashed_password.startswith("sha256$"):
                # Verify simple SHA256 fallback hash
                try:
                    import hashlib
                    stored_hash = hashed_password.replace("sha256$", "")
                    computed_hash = hashlib.sha256(plain_password.encode()).hexdigest()
                    result = computed_hash == stored_hash
                    logger.debug(f"SHA256 verification {'succeeded' if result else 'failed'}")
                    return result
                except Exception as e:
                    logger.error(f"SHA256 verification failed: {str(e)}")
                    return False
                    
            else:
                # Try bcrypt verification (original format)
                try:
                    result = pwd_context.verify(plain_password, hashed_password)
                    logger.debug(f"bcrypt verification {'succeeded' if result else 'failed'}")
                    return result
                except AttributeError as e:
                    if "'__about__'" in str(e) or "module 'bcrypt' has no attribute" in str(e):
                        logger.warning("bcrypt verification failed due to compatibility issue")
                        return False
                    else:
                        logger.error(f"Unexpected bcrypt AttributeError: {str(e)}")
                        return False
                except Exception as e:
                    logger.warning(f"bcrypt verification failed: {str(e)}")
                    return False
                    
        except Exception as e:
            logger.error(f"Password verification completely failed: {str(e)}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password with robust error handling and fallbacks"""
        try:
            # Truncate password to 72 bytes to avoid bcrypt limitation
            if len(password.encode('utf-8')) > 72:
                password = password[:72]
                logger.warning(f"Password truncated to 72 bytes for bcrypt compatibility")
            
            # Try bcrypt hashing first with improved error handling
            try:
                hashed = pwd_context.hash(password)
                logger.debug("Password hashed using bcrypt")
                return hashed
            except AttributeError as e:
                if "'__about__'" in str(e) or "module 'bcrypt' has no attribute" in str(e):
                    logger.warning("bcrypt library compatibility issue detected, using fallback method")
                    return self._fallback_hash(password)
                else:
                    logger.error(f"Unexpected AttributeError in bcrypt: {str(e)}")
                    return self._fallback_hash(password)
            except Exception as e:
                logger.warning(f"bcrypt hashing failed: {str(e)}, using fallback method")
                return self._fallback_hash(password)
                
        except Exception as e:
            logger.error(f"Password hashing failed completely: {str(e)}")
            return self._fallback_hash(password)
    
    def _set_bcrypt_backend(self) -> None:
        """Set bcrypt backend to avoid compatibility issues"""
        try:
            # Try to explicitly set the backend to avoid __about__ errors
            import bcrypt
            # Check if __about__ exists, if not, we have a compatibility issue
            if not hasattr(bcrypt, '__about__'):
                logger.warning("bcrypt library missing __about__ attribute, forcing fallback")
                return False
            return True
        except Exception as e:
            logger.warning(f"bcrypt backend check failed: {str(e)}")
            return False
    
    def _fallback_hash(self, password: str) -> str:
        """Fallback hashing method using pbkdf2_sha256"""
        try:
            import hashlib
            import secrets
            salt = secrets.token_hex(16)
            iterations = 100000
            pbkdf2_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations).hex()
            logger.debug("Password hashed using pbkdf2_sha256 fallback")
            return f"pbkdf2_sha256${iterations}${salt}${pbkdf2_hash}"
        except Exception as e:
            logger.error(f"Fallback hashing failed: {str(e)}")
            # Final fallback to simple SHA256
            import hashlib
            return f"sha256${hashlib.sha256(password.encode()).hexdigest()}"
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify JWT token and extract user ID"""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenData(user_id=user_id)
        
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def register_user(self, user_data: UserRegister) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = await self.db_ops.get_user_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create user with hashed password
            hashed_password = self.get_password_hash(user_data.password)
            
            user_doc = UserDocument(
                username=user_data.username,
                email=user_data.email,
                password_hash=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                role="user",
                is_active=True,
                is_email_verified=False
            )
            
            user_id = await self.db_ops.create_user(user_doc)
            
            # Create tokens
            token_data = {"sub": str(user_id)}
            access_token = self.create_access_token(token_data)
            refresh_token = self.create_refresh_token(token_data)
            
            logger.info(f"User registered successfully: {user_data.email}")
            
            return {
                "success": True,
                "message": "User registered successfully",
                "user_id": user_id,
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": settings.jwt_access_token_expire_minutes * 60
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    async def login_user(self, login_data: UserLogin) -> Dict[str, Any]:
        """Login user and return tokens"""
        try:
            # Get user by email
            user = await self.db_ops.get_user_by_email(login_data.email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is disabled"
                )
            
            # Verify password
            if not user.password_hash or not self.verify_password(login_data.password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Update last login
            await self.db_ops.update_user(user.user_id, {"last_login": datetime.utcnow()})
            
            # Create tokens
            token_data = {"sub": str(user.user_id)}
            access_token = self.create_access_token(token_data)
            refresh_token = self.create_refresh_token(token_data)
            
            logger.info(f"User logged in successfully: {login_data.email}")
            
            return {
                "success": True,
                "message": "Login successful",
                "user": self._user_to_response(user),
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": settings.jwt_access_token_expire_minutes * 60
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt.decode(refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            token_type: str = payload.get("type")
            
            if token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Create new access token
            token_data = {"sub": str(user_id)}
            new_access_token = self.create_access_token(token_data)
            
            return {
                "success": True,
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.jwt_access_token_expire_minutes * 60
            }
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed"
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID"""
        try:
            user = await self.db_ops.get_user_by_id(user_id)
            if user:
                return self._user_to_response(user)
            return None
        except Exception as e:
            logger.error(f"Failed to get user by ID: {str(e)}")
            return None
    
    def _user_to_response(self, user: UserDocument) -> UserResponse:
        """Convert UserDocument to UserResponse"""
        return UserResponse(
            user_id=str(user.user_id),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            created_at=user.created_at,
            last_login=user.last_login
        )
    
    async def verify_user_email(self, user_id: str) -> bool:
        """Verify user email"""
        try:
            return await self.db_ops.update_user(user_id, {"is_email_verified": True})
        except Exception as e:
            logger.error(f"Failed to verify email: {str(e)}")
            return False
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        try:
            # Get user
            user = await self.db_ops.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify old password
            if not user.password_hash or not self.verify_password(old_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid old password"
                )
            
            # Hash new password
            new_hashed_password = self.get_password_hash(new_password)
            
            # Update password
            success = await self.db_ops.update_user(user_id, {"password_hash": new_hashed_password})
            
            if success:
                logger.info(f"Password changed successfully for user: {user_id}")
                return {"success": True, "message": "Password changed successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update password"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password change failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password change failed"
            )

# Global authentication service instance
auth_service = AuthService()