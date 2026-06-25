# Document Embedding & Search Service

Upload documents, embed them locally, search by meaning with pgvector.

```bash
docker compose up -d --build
```

- Frontend: http://localhost:3000  
- Backend: http://localhost:8000  
- Health: `curl http://localhost:8000/api/health/`

Stop: `docker compose down` · Reset data: `docker compose down -v`

---

## What it does

1. Upload `.txt`, `.md`, `.pdf`, or `.docx` files (staged upload in the UI).
2. A Celery worker extracts text, chunks, embeds with `BAAI/bge-small-en-v1.5`, stores vectors in PostgreSQL.
3. Search by natural-language query; results above a relevance threshold with optional document scope filter.
4. Open a result to see highlighted text, surrounding chunks, extracted full text, or download the original file.

No external API keys required.

---

## Stack

Django + DRF · Celery + Redis · PostgreSQL 16 + pgvector · Next.js 14 · local sentence-transformers (CPU)

---

## Documentation

Full design and API details live in [`docs/`](docs/README.md):

- [Architecture](docs/architecture.md) — how the system works and why
- [Embeddings](docs/embeddings.md) — why the model runs locally
- [Chunking strategy](docs/chunking-strategy.md) — token size, overlap, format-aware splits
- [API reference](docs/api.md)
- [Configuration](docs/configuration.md)

---

## Quick API examples

```bash
# Upload
curl -X POST http://localhost:8000/api/documents/ -F "files=@notes.md"

# Search
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"refund policy","limit":10}'

# Download original
curl -O -J http://localhost:8000/api/documents/1/download/
```

---

## Django admin

```bash
docker compose exec backend python manage.py createsuperuser
```

http://localhost:8000/admin/
