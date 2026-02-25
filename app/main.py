from fastapi import FastAPI, HTTPException

from app.rag_service import RAGService
from app.schemas import AskRequest, AskResponse, HealthResponse, IngestRequest, IngestResponse
from app.settings import settings


app = FastAPI(title=settings.app_name, version=settings.app_version)
service = RAGService()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(**service.health())


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest) -> IngestResponse:
    try:
        doc_id, total_docs, index_updated = service.ingest(text=payload.text, source=payload.source)
        return IngestResponse(document_id=doc_id, total_documents=total_docs, index_updated=index_updated)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    try:
        answer, sources, used_top_k = service.ask(question=payload.question, top_k=payload.top_k)
        return AskResponse(answer=answer, sources=sources, used_top_k=used_top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
