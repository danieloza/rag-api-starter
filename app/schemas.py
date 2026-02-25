from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    document_id: str
    total_documents: int
    index_updated: bool


class AskRequest(BaseModel):
    question: str = Field(min_length=1, description="User question")
    top_k: int | None = Field(default=None, ge=1, le=10)


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    used_top_k: int


class HealthResponse(BaseModel):
    status: str
    ready: bool
    documents: int
    embedding_model: str
    vector_store: str
