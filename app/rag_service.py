import json
import threading
import uuid
from datetime import datetime, timezone

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.settings import settings


def _detect_device() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


class RAGService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._embeddings: HuggingFaceEmbeddings | None = None
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        if not settings.docs_store_file.exists():
            settings.docs_store_file.write_text("", encoding="utf-8")

    def _read_jsonl(self) -> list[dict]:
        rows: list[dict] = []
        if not settings.docs_store_file.exists():
            return rows
        with settings.docs_store_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows

    def _write_jsonl_record(self, record: dict) -> None:
        with settings.docs_store_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=True) + "\n")

    def _to_documents(self, rows: list[dict]) -> list[Document]:
        return [
            Document(
                page_content=row["text"],
                metadata={
                    "source": row.get("source", "manual"),
                    "document_id": row.get("id", "unknown"),
                    "created_at": row.get("created_at", "unknown"),
                },
            )
            for row in rows
        ]

    def _get_embeddings(self) -> HuggingFaceEmbeddings:
        if self._embeddings is None:
            device = settings.embedding_device or _detect_device()
            self._embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={"device": device},
                encode_kwargs={"normalize_embeddings": True},
            )
        return self._embeddings

    def _split_documents(self, docs: list[Document]) -> list[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        return splitter.split_documents(docs)

    def _rebuild_index(self) -> bool:
        rows = self._read_jsonl()
        if not rows:
            return False

        docs = self._to_documents(rows)
        split_docs = self._split_documents(docs)
        embeddings = self._get_embeddings()
        vector_store = FAISS.from_documents(split_docs, embeddings)
        vector_store.save_local(str(settings.index_dir))
        return True

    def _index_exists(self) -> bool:
        return settings.index_dir.exists() and any(settings.index_dir.iterdir())

    def count_documents(self) -> int:
        return len(self._read_jsonl())

    def ingest(self, text: str, source: str) -> tuple[str, int, bool]:
        with self._lock:
            record = {
                "id": str(uuid.uuid4()),
                "text": text,
                "source": source,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._write_jsonl_record(record)
            updated = self._rebuild_index()
            return record["id"], self.count_documents(), updated

    def ask(self, question: str, top_k: int | None = None) -> tuple[str, list[str], int]:
        if not self._index_exists():
            raise ValueError("Index not found. Ingest data first using POST /ingest.")

        used_top_k = top_k if top_k is not None else settings.retrieval_k
        used_top_k = max(1, min(used_top_k, settings.max_top_k))
        min_score = settings.retrieval_score_threshold

        embeddings = self._get_embeddings()
        vector_store = FAISS.load_local(
            str(settings.index_dir),
            embeddings,
            allow_dangerous_deserialization=True,
        )

        scored_docs = vector_store.similarity_search_with_relevance_scores(
            question,
            k=used_top_k,
        )
        filtered_docs = [doc for doc, score in scored_docs if score is not None and score >= min_score]

        if not filtered_docs:
            return (
                f"No context passed threshold {min_score:.2f}. Try lowering threshold or ingesting richer documents.",
                [],
                used_top_k,
            )

        context_snippets = [doc.page_content.strip().replace("\n", " ") for doc in filtered_docs[:2]]
        merged = " ".join(context_snippets)
        answer = f"Based on retrieved context: {merged[:500]}"

        sources = sorted({str(doc.metadata.get("source", "manual")) for doc in filtered_docs})
        return answer, sources, used_top_k

    def health(self) -> dict:
        docs = self.count_documents()
        return {
            "status": "ok",
            "ready": self._index_exists(),
            "documents": docs,
            "embedding_model": settings.embedding_model,
            "vector_store": "faiss",
            "retrieval_score_threshold": settings.retrieval_score_threshold,
        }
