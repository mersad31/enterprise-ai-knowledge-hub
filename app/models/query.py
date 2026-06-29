from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)
    document_id: str | None = None


class SearchHit(BaseModel):
    text: str
    document_id: str | None = None
    score: float
    metadata: dict


class QueryResponse(BaseModel):
    results: list[SearchHit]