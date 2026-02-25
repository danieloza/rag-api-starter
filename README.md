# RAG API Starter

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Store-0467DF)](https://github.com/facebookresearch/faiss)

Production-style mini project for GenAI/RAG interviews: ingest local knowledge, build a vector index, and answer grounded questions.

## 15-Second Pitch
- FastAPI service with `POST /ingest`, `POST /ask`, `GET /health`.
- Persistent local document store (`data/knowledge.jsonl`) + FAISS index rebuild.
- Default `FAKE_MODE` for a reliable 2-minute demo, optional real model mode.

## Demo In 2 Minutes
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

## Quick API Flow
Ingest one document:
```bash
curl -X POST http://127.0.0.1:8010/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"portfolio","text":"Daniel builds FastAPI multi-tenant systems and automation bots."}'
```

Ask a question:
```bash
curl -X POST http://127.0.0.1:8010/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What does Daniel build?"}'
```

PowerShell examples:
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8010/ingest -ContentType 'application/json' -Body '{"source":"portfolio","text":"Daniel builds FastAPI multi-tenant systems and automation bots."}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8010/ask -ContentType 'application/json' -Body '{"question":"What does Daniel build?"}'
```

## Demo Proof
Swagger/API docs:

![Swagger docs](docs/assets/demo-docs.png)

Health endpoint:

![Health endpoint](docs/assets/demo-health.png)

## Real Model Mode (Optional)
Default mode is `RAG_FAKE_MODE=true` for stable local demos.

To run real embedding + generation models:
1. `pip install -r requirements-real.txt`
2. Set `RAG_FAKE_MODE=false` in `.env`
3. Restart API

## Project Structure
- `app/main.py` - FastAPI routes
- `app/rag_service.py` - ingestion, indexing, retrieval, answer generation
- `app/settings.py` - app configuration
- `app/schemas.py` - API contracts
- `data/` - local document store and FAISS index

## Release and License
- Release: `v0.1.0`
- License: `MIT` (see `LICENSE`)
- Changelog: `CHANGELOG.md`
