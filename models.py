from pydantic import BaseModel
from typing import List, Optional

class IngestPayload(BaseModel):
    documentId: str
    userId: str
    document: str
    title: str
    

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