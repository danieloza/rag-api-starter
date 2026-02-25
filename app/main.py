from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from app.rag_service import RAGService
from app.schemas import AskRequest, AskResponse, HealthResponse, IngestPayload, IngestResponse
from app.settings import settings


app = FastAPI(title=settings.app_name, version=settings.app_version)
service = RAGService()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(**service.health())


@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
    source: str | None = Form(default=None),
) -> IngestResponse:
    if file is None and (text is None or not text.strip()):
        raise HTTPException(status_code=400, detail="Provide either 'file' or non-empty 'text'.")

    document_text = ""
    resolved_source = source if source else "manual"

    try:
        if file is not None:
            file_bytes = await file.read()
            document_text = file_bytes.decode("utf-8-sig", errors="ignore")
            if not source:
                resolved_source = file.filename or "upload"
        else:
            document_text = text or ""

        payload = IngestPayload(text=document_text, source=resolved_source)
        doc_id, total_docs, index_updated = service.ingest(text=payload.text, source=payload.source)
        return IngestResponse(document_id=doc_id, total_documents=total_docs, index_updated=index_updated)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except HTTPException:
        raise
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
