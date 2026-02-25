import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings

from app.settings import settings


class RAGService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
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

    def _get_embeddings(self):
        if settings.rag_fake_mode:
            return FakeEmbeddings(size=384)

        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            encode_kwargs={"normalize_embeddings": True},
        )

    def _build_prompt(self, context: str, question: str) -> str:
        return (
            "You are a retrieval assistant. Use only the context to answer. "
            "If context is insufficient, say what is missing.\n\n"
            f"Context:\n{context}\n\n"
            f"Question:\n{question}\n\n"
            "Answer:"
        )

    def _generate_answer(self, question: str, context: str) -> str:
        if settings.rag_fake_mode:
            summary = context[:400].replace("\n", " ").strip()
            if not summary:
                return "No relevant context found in the current index."
            return f"FAKE_MODE answer: based on indexed context -> {summary}"

        from langchain_huggingface import HuggingFacePipeline
        from transformers import pipeline

        prompt = self._build_prompt(context=context, question=question)
        generator = pipeline(
            task="text2text-generation",
            model=settings.llm_model,
            max_new_tokens=220,
            do_sample=False,
        )
        llm = HuggingFacePipeline(pipeline=generator)
        return llm.invoke(prompt)

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

        embeddings = self._get_embeddings()
        vector_store = FAISS.load_local(
            str(settings.index_dir),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        retriever = vector_store.as_retriever(search_kwargs={"k": used_top_k})
        docs = retriever.invoke(question)

        context = "\n\n".join(doc.page_content for doc in docs)
        answer = self._generate_answer(question=question, context=context)

        sources = sorted({str(doc.metadata.get("source", "manual")) for doc in docs})
        return answer, sources, used_top_k

    def health(self) -> dict:
        docs = self.count_documents()
        return {
            "status": "ok",
            "ready": self._index_exists(),
            "fake_mode": settings.rag_fake_mode,
            "documents": docs,
            "embedding_model": settings.embedding_model,
            "llm_model": settings.llm_model,
        }
