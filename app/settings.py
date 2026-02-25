from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "RAG API Starter"
    app_version: str = "0.1.0"

    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    docs_store_file: Path = data_dir / "knowledge.jsonl"
    index_dir: Path = data_dir / "index"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"

    chunk_size: int = 400
    chunk_overlap: int = 60
    retrieval_k: int = 3
    retrieval_score_threshold: float = Field(default=0.15, ge=0.0, le=1.0)
    max_top_k: int = 10


settings = Settings()
