from pydantic import BaseModel, Field


class DocumentIn(BaseModel):
    text: str = Field(..., min_length=1)
    filename: str | None = None


class DocumentOut(BaseModel):
    document_id: str
    chunk_count: int
    chunk_ids: list[str]