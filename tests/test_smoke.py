import sys
import types
import asyncio


fake_rag_service = types.ModuleType("app.rag_service")


class BootstrapService:
    def ingest(self, text: str, source: str) -> tuple[str, int, bool]:
        return "bootstrap", 0, False

    def ask(self, question: str, top_k: int | None = None) -> tuple[str, list[str], int]:
        return "bootstrap", [], top_k or 3

    def health(self) -> dict:
        return {
            "status": "ok",
            "ready": True,
            "documents": 0,
            "embedding_model": "stub",
            "vector_store": "faiss",
            "retrieval_score_threshold": 0.15,
        }


fake_rag_service.RAGService = BootstrapService
sys.modules.setdefault("app.rag_service", fake_rag_service)

import app.main as main
from app.schemas import AskRequest


class DummyService:
    def __init__(self) -> None:
        self.last_ingest: tuple[str, str] | None = None

    def ingest(self, text: str, source: str) -> tuple[str, int, bool]:
        self.last_ingest = (text, source)
        return "doc-smoke-1", 1, True

    def ask(self, question: str, top_k: int | None = None) -> tuple[str, list[str], int]:
        used_top_k = top_k if top_k is not None else 3
        return f"echo: {question}", ["portfolio"], used_top_k


def test_ingest_smoke_text_mode(monkeypatch) -> None:
    service = DummyService()
    monkeypatch.setattr(main, "service", service)
    response = asyncio.run(main.ingest(file=None, text="  Hello from smoke  ", source="  portfolio  "))

    assert response.document_id == "doc-smoke-1"
    assert response.total_documents == 1
    assert response.index_updated is True
    assert service.last_ingest == ("Hello from smoke", "portfolio")


def test_ask_smoke_with_top_k(monkeypatch) -> None:
    monkeypatch.setattr(main, "service", DummyService())
    response = main.ask(AskRequest(question="What is this API?", top_k=4))

    assert response.sources == ["portfolio"]
    assert response.used_top_k == 4
    assert response.answer.startswith("echo:")
