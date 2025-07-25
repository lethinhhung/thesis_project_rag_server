from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from models import User, TokenData
import json
import uuid

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 Bearer
security = HTTPBearer()

# In-memory user storage (replace with database in production)
# Using Pinecone metadata field or file storage for persistence
USERS_DB_FILE = "users.json"

def load_users_db() -> Dict[str, Any]:
    """Load users from file storage"""
    try:
        if os.path.exists(USERS_DB_FILE):
            with open(USERS_DB_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

def save_users_db(users_db: Dict[str, Any]) -> None:
    """Save users to file storage"""
    try:
        with open(USERS_DB_FILE, 'w') as f:
            json.dump(users_db, f, default=str, indent=2)
    except Exception as e:
        print(f"Error saving users database: {e}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_user(email: str, username: str, password: str, full_name: Optional[str] = None) -> User:
    """Create a new user"""
    users_db = load_users_db()
    
    # Check if user already exists
    if email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    for user_data in users_db.values():
        if user_data.get("username") == username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Create new user
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    user_data = {
        "id": user_id,
        "email": email,
        "username": username,
        "full_name": full_name,
        "hashed_password": get_password_hash(password),
        "is_active": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    users_db[email] = user_data
    save_users_db(users_db)
    
    return User(
        id=user_id,
        email=email,
        username=username,
        full_name=full_name,
        is_active=True,
        created_at=now,
        updated_at=now
    )

def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    users_db = load_users_db()
    
    if email not in users_db:
        return None
    
    user_data = users_db[email]
    if not verify_password(password, user_data["hashed_password"]):
        return None
    
    return User(
        id=user_data["id"],
        email=user_data["email"],
        username=user_data["username"],
        full_name=user_data.get("full_name"),
        is_active=user_data["is_active"],
        created_at=datetime.fromisoformat(user_data["created_at"]),
        updated_at=datetime.fromisoformat(user_data["updated_at"])
    )

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

def verify_token(token: str) -> TokenData:
    """Verify JWT token and return token data"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(email=email)
        return token_data
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email"""
    users_db = load_users_db()
    
    if email not in users_db:
        return None
    
    user_data = users_db[email]
    return User(
        id=user_data["id"],
        email=user_data["email"],
        username=user_data["username"],
        full_name=user_data.get("full_name"),
        is_active=user_data["is_active"],
        created_at=datetime.fromisoformat(user_data["created_at"]),
        updated_at=datetime.fromisoformat(user_data["updated_at"])
    )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    token_data = verify_token(token)
    user = get_user_by_email(email=token_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user