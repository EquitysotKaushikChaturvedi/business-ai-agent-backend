from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    business_id: str
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    business_id: str

class IngestResponse(BaseModel):
    filename: str
    status: str
    chunks_processed: int
    message: str
