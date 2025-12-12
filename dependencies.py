from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from auth import AuthService
from models import User, TokenData
from typing import Optional

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={
        "read": "Read access to user data",
        "write": "Write access to user data",
        "admin": "Administrative access"
    }
)

class AuthenticationError(HTTPException):
    """Custom authentication exception"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class PermissionError(HTTPException):
    """Custom permission exception"""
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        token_data = AuthService.verify_token(token)
        if token_data is None:
            raise credentials_exception
        
        username: str = token_data.username
        user_id: str = token_data.user_id
        token_scopes: list = token_data.scopes
        
    except Exception:
        raise credentials_exception
    
    user = AuthService.get_user(username=username)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Check scopes
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    
    # Convert UserInDB to User for response
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get admin user (requires admin scope)
    """
    # This would typically check for admin role/scope
    # For now, we'll check if username is admin
    if current_user.username != "admin":
        raise PermissionError("Admin access required")
    return current_user

async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    Dependency to optionally get current user (doesn't fail if no token)
    """
    if token is None:
        return None
    
    try:
        token_data = AuthService.verify_token(token)
        if token_data is None:
            return None
        
        user = AuthService.get_user(username=token_data.username)
        if user is None or not user.is_active:
            return None
        
        return User(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    except Exception:
        return None

# Utility function to validate user ownership
def validate_user_access(current_user: User, resource_user_id: str):
    """
    Validate that current user has access to resource
    (either owns it or is admin)
    """
    if current_user.id != resource_user_id and current_user.username != "admin":
        raise PermissionError("Access denied to this resource")

# Middleware dependencies for different access levels
RequireAuth = Depends(get_current_active_user)
RequireAdmin = Depends(get_admin_user)
OptionalAuth = Depends(get_optional_current_user)