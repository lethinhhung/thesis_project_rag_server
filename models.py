from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Authentication Models
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None

# Existing Models
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