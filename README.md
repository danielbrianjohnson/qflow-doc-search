# Document Embedding & Search Service

Small end-to-end semantic search service:
- upload documents (`.txt`, `.md`, `.pdf`, `.docx`)
- embed content locally (no external API keys)
- search by meaning with pgvector

Run with one command:

```bash
docker compose up -d --build
```

Frontend: `http://localhost:3000`  
Backend: `http://localhost:8000`

---

## Quick Start

```bash
git clone <repo-url>
cd qflow-assessment
docker compose up -d --build
curl http://localhost:8000/api/health/
```

Stop:

```bash
docker compose down
docker compose down -v  # wipe volumes
```

---

## Stack

- Backend: Django + DRF
- Worker: Celery + Redis
- Database: PostgreSQL 16 + pgvector (HNSW index)
- Embeddings: `BAAI/bge-small-en-v1.5` (local via sentence-transformers)
- Frontend: Next.js 14 + Tailwind
- Storage: local Docker volume at `/app/uploads` (S3/MinIO recommended for production)

---

## Core Flow

1. User uploads one or more files.
2. API validates and stores files, creates `Document(status=queued)`.
3. Celery worker extracts text, chunks, embeds, stores vectors, sets `status=ready`.
4. Search endpoint embeds query and runs cosine similarity search in pgvector.
5. UI shows top results above configured threshold, with context modal.

---

## API (minimal)

Base URL: `http://localhost:8000/api`

- `GET /health/`
- `POST /documents/` (multipart `files`)
- `GET /documents/`
- `GET /documents/{id}/`
- `GET /documents/{id}/content/` (truncated text view)
- `DELETE /documents/{id}/`
- `POST /search/`
- `GET /documents/{id}/chunks/{chunk_index}/context/` (match ±1 chunk)

Example search:

```bash
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"refund policy","limit":10,"document_ids":[1,3]}'
```

Notes:
- `min_score` is backend-configured (`SEARCH_MIN_SCORE`), not a request parameter.
- Response includes `min_score`, `total_above_threshold`, and `results`.

---

## Config (important env vars)

- `MAX_UPLOAD_SIZE_MB` (default `50`)
- `MAX_FILES_PER_UPLOAD` (default `10`)
- `MAX_TOTAL_DOCUMENTS` (default `100`)
- `ALLOWED_EXTENSIONS` (default `txt,md,pdf,docx`)
- `EMBEDDING_MODEL` (default `BAAI/bge-small-en-v1.5`)
- `CHUNK_SIZE_TOKENS` (default `512`)
- `CHUNK_OVERLAP_TOKENS` (default `64`)
- `SEARCH_DEFAULT_LIMIT` (default `10`)
- `SEARCH_MIN_SCORE` (default `0.5`)
- `SEARCH_CANDIDATE_MULTIPLIER` (default `3`)
- `DOCUMENT_CONTENT_MAX_CHARS` (default `120000`)

See `docker-compose.yml` for full defaults.

---

## UX choices

- Search-first page with staged upload (`Start upload`)
- Multi-select document scope (empty = all docs)
- Recent uploads panel (latest 8)
- Result modal with highlighted passage, surrounding chunks, optional full document text
- Delete requires confirmation

---

## If More Time

- Move file storage to S3/MinIO
- Add hybrid retrieval (BM25 + vector rerank)
- Add SSE push updates (replace polling)
- Add integration tests + CI
- Add observability and auth

---

**Detailed docs:** [README_LONG.md](README_LONG.md) — architecture, design decisions, full API reference, scaling notes.
