from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)
    document_id: str | None = None

class ChatResponse(BaseModel):
    answer: str
    sources: list
    model_used: str