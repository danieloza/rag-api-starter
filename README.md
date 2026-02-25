# RAG API Starter

Minimal, production-style MVP RAG service that works fully local with no paid APIs.

## MVP Scope (End-to-End)
- `POST /ingest` - upload a document (`.txt`) to the knowledge base
- `POST /ask` - ask a question and get `answer + sources`
- `GET /health` - readiness and index status

Stack:
- FastAPI
- Hugging Face embeddings (`sentence-transformers/all-MiniLM-L6-v2`)
- FAISS vector store (local disk)

## Run Locally (2 Minutes)
```bash
git clone https://github.com/danieloza/rag-api-starter.git
cd rag-api-starter
python -m venv .venv
```

Activate virtual environment:
```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Install and run:
```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

Windows alternative for env copy:
```powershell
Copy-Item .env.example .env
```

Open:
- `http://127.0.0.1:8010/docs`
- `http://127.0.0.1:8010/health`

## End-to-End Demo Flow
Upload a document:
```bash
curl -X POST http://127.0.0.1:8010/ingest \
  -F "file=@docs/sample.txt" \
  -F "source=portfolio"
```

Ask a question:
```bash
curl -X POST http://127.0.0.1:8010/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What does Daniel build?","top_k":3}'
```

PowerShell examples:
```powershell
curl.exe -X POST "http://127.0.0.1:8010/ingest" -F "file=@docs/sample.txt" -F "source=portfolio"
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8010/ask -ContentType 'application/json' -Body '{"question":"What does Daniel build?","top_k":3}'
```

## Demo Proof
Swagger/API docs:

![Swagger docs](docs/assets/demo-docs.png)

Health endpoint:

![Health endpoint](docs/assets/demo-health.png)

## API Contracts
- `POST /ingest` (multipart form)
  - `file` (required for document upload)
  - `source` (optional string)
- `POST /ask` (JSON)
  - `question` (required)
  - `top_k` (optional, default from config)

Example `/ask` response:
```json
{
  "answer": "Based on retrieved context: ...",
  "sources": ["portfolio"],
  "used_top_k": 3
}
```

## Project Structure
- `app/main.py` - FastAPI routes
- `app/rag_service.py` - ingestion, indexing, retrieval, answer assembly
- `app/settings.py` - runtime config
- `app/schemas.py` - response/request models
- `data/` - local FAISS index + knowledge store

## Release and License
- Release: `v0.1.0`
- License: `MIT` (see `LICENSE`)
- Changelog: `CHANGELOG.md`
