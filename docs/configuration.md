# Configuration

Environment variables are set in `docker-compose.yml`. Override there or via a `.env` file for local experiments.

---

## Upload and storage

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_UPLOAD_SIZE_MB` | `50` | Max size per file |
| `MAX_FILES_PER_UPLOAD` | `10` | Max files in one POST |
| `MAX_TOTAL_DOCUMENTS` | `100` | Max documents in the system |
| `ALLOWED_EXTENSIONS` | `txt,md,pdf,docx` | Comma-separated extensions |

---

## Embeddings and chunking

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | sentence-transformers model ID |
| `CHUNK_SIZE_TOKENS` | `512` | Target tokens per chunk |
| `CHUNK_OVERLAP_TOKENS` | `64` | Token overlap when sliding long sections |

See [Embeddings](embeddings.md) and [Chunking strategy](chunking-strategy.md) for rationale.

---

## Search

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARCH_DEFAULT_LIMIT` | `10` | Default `limit` when omitted in POST `/search/` |
| `SEARCH_MAX_LIMIT` | `50` | Hard cap on `limit` (not env-exposed in compose; set in `settings.py`) |
| `SEARCH_MIN_SCORE` | `0.5` | Minimum cosine similarity to include a result |
| `SEARCH_CANDIDATE_MULTIPLIER` | `3` | Fetch `limit × multiplier` ANN candidates before threshold filter |

---

## Content API

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCUMENT_CONTENT_MAX_CHARS` | `120000` | Max characters returned by `GET .../content/` (UI preview only; does not affect embedding) |

---

## Infrastructure (compose)

| Service | Notes |
|---------|-------|
| `db` | PostgreSQL 16 + pgvector image |
| `redis` | Celery broker |
| `backend` | Django `web` role — runs migrations |
| `worker` | Celery — no migrations |
| `frontend` | Next.js; `NEXT_PUBLIC_API_URL` points at backend |

Rebuild after changing backend env vars:

```bash
docker compose up -d --build backend worker
```

Frontend-only changes:

```bash
docker compose up -d --build frontend
```
