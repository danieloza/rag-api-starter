from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    text: str = Field(min_length=1, description="Raw text to add to the knowledge base")
    source: str = Field(default="manual", min_length=1, description="Document source label")


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
    fake_mode: bool
    documents: int
    embedding_model: str
    llm_model: str
