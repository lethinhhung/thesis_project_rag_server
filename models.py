from pydantic import BaseModel, EmailStr
from typing import List, Optional, Union
from datetime import datetime

# Existing models
class IngestPayload(BaseModel):
    documentId: str
    userId: str
    document: str
    title: str
    courseId: Optional[str] = None
    courseTitle: Optional[str] = None
    

class QuestionPayload(BaseModel):
    userId: str
    query: str

class DeletePayload(BaseModel):
    documentId: str
    userId: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionPayload(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "deepseek-r1-distill-llama-70b"
    userId: str
    isUseKnowledge: Optional[bool] = False
    courseId: Optional[str] = None
    courseTitle: Optional[str] = None

# Authentication models
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None
    scopes: List[str] = []

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LoginRequest(BaseModel):
    username: str
    password: str
    grant_type: Optional[str] = "password"
    scope: Optional[str] = ""

class OAuth2PasswordRequestForm(BaseModel):
    username: str
    password: str
    scope: str = ""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None