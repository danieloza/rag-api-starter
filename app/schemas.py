from pydantic import BaseModel, Field, field_validator


class IngestPayload(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    source: str = Field(default="manual", min_length=1, max_length=120)

    @field_validator("text", "source", mode="before")
    @classmethod
    def strip_and_validate_non_empty(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned


class IngestResponse(BaseModel):
    document_id: str
    total_documents: int
    index_updated: bool


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000, description="User question")
    top_k: int | None = Field(default=None, ge=1, le=10)

    @field_validator("question", mode="before")
    @classmethod
    def strip_question(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("question must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("question must not be empty")
        return cleaned


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
    retrieval_score_threshold: float
