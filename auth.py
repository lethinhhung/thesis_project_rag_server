from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from models import UserInDB, TokenData, User, UserCreate
import os
from dotenv import load_dotenv

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# In-memory user database (replace with real database in production)
fake_users_db: Dict[str, UserInDB] = {}
refresh_tokens_db: Dict[str, Dict[str, Any]] = {}

class AuthService:
    """Authentication service for handling OAuth2 operations"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def get_user(username: str) -> Optional[UserInDB]:
        """Get user by username"""
        return fake_users_db.get(username)
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        for user in fake_users_db.values():
            if user.id == user_id:
                return user
        return None
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with username and password"""
        user = AuthService.get_user(username)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def create_user(user_data: UserCreate) -> UserInDB:
        """Create a new user"""
        if user_data.username in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists
        for existing_user in fake_users_db.values():
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        hashed_password = AuthService.get_password_hash(user_data.password)
        user_id = str(uuid.uuid4())
        
        db_user = UserInDB(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            is_active=user_data.is_active,
            hashed_password=hashed_password,
            created_at=datetime.now(timezone.utc)
        )
        
        fake_users_db[user_data.username] = db_user
        return db_user
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create refresh token"""
        refresh_token_id = str(uuid.uuid4())
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        refresh_tokens_db[refresh_token_id] = {
            "user_id": user_id,
            "expires_at": expire,
            "is_active": True
        }
        
        return refresh_token_id
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verify JWT token and return token data"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            scopes: list = payload.get("scopes", [])
            
            if username is None or user_id is None:
                return None
            
            token_data = TokenData(
                username=username,
                user_id=user_id,
                scopes=scopes
            )
            return token_data
        except JWTError:
            return None
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[dict]:
        """Generate new access token from refresh token"""
        refresh_data = refresh_tokens_db.get(refresh_token)
        
        if not refresh_data or not refresh_data["is_active"]:
            return None
        
        if datetime.now(timezone.utc) > refresh_data["expires_at"]:
            # Refresh token expired, remove it
            refresh_tokens_db.pop(refresh_token, None)
            return None
        
        user = AuthService.get_user_by_id(refresh_data["user_id"])
        if not user or not user.is_active:
            return None
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "scopes": []
            },
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_token": refresh_token
        }
    
    @staticmethod
    def revoke_refresh_token(refresh_token: str) -> bool:
        """Revoke a refresh token"""
        if refresh_token in refresh_tokens_db:
            refresh_tokens_db[refresh_token]["is_active"] = False
            return True
        return False
    
    @staticmethod
    def revoke_all_user_tokens(user_id: str) -> int:
        """Revoke all refresh tokens for a user"""
        revoked_count = 0
        for token_data in refresh_tokens_db.values():
            if token_data["user_id"] == user_id and token_data["is_active"]:
                token_data["is_active"] = False
                revoked_count += 1
        return revoked_count

# Initialize with a default admin user for testing
def init_default_user():
    """Initialize default admin user"""
    if "admin" not in fake_users_db:
        admin_user = UserCreate(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            password="admin123",
            is_active=True
        )
        try:
            AuthService.create_user(admin_user)
        except HTTPException:
            pass  # User already exists

# Call initialization
init_default_user()