from pydantic import BaseModel

class IngestPayload(BaseModel):
    documentId: str
    userId: str
    document: str
    

class QuestionPayload(BaseModel):
    userId: str
    query: str

class DeletePayload(BaseModel):
    documentId: str
    userId: str

class ChatCompletionPayload(BaseModel):
    userId: str
    query: str
    messages: list[dict]