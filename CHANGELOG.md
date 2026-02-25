# Changelog

All notable changes to this project are documented in this file.

## [v0.1.1] - 2026-02-25
### Changed
- Upgraded MVP to strict local RAG flow with Hugging Face embeddings + FAISS.
- `POST /ingest` now supports real document upload (multipart file).
- Removed fake mode path from runtime logic.

## [v0.1.0] - 2026-02-25
### Added
- FastAPI mini-RAG service with `/ingest`, `/ask`, `/health`.
- Persistent JSONL knowledge store and FAISS index rebuild flow.
- Demo-first README, release baseline, and MIT license.
