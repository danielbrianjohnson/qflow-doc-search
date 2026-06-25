# API reference

Base URL: `http://localhost:8000/api`

Rate limits (per IP): 10 uploads/min, 60 searches/min.

---

## Health

```bash
curl http://localhost:8000/api/health/
```

```json
{
  "status": "ok",
  "database": "ok",
  "embedding_model": "ready"
}
```

---

## Documents

### Upload (multi-file)

```bash
curl -X POST http://localhost:8000/api/documents/ \
  -F "files=@report.pdf" -F "files=@notes.md"
```

Returns `202 Accepted`. Documents start as `status: queued`; Celery processes them asynchronously.

### List

```bash
curl http://localhost:8000/api/documents/
```

Paginated (`results` array) when using default DRF pagination.

### Get / delete

```bash
curl http://localhost:8000/api/documents/1/
curl -X DELETE http://localhost:8000/api/documents/1/
```

Delete removes the file from disk, all chunks, and embeddings.

### Download original file

```bash
curl -O -J http://localhost:8000/api/documents/1/download/
```

Returns the uploaded file with `Content-Disposition: attachment`. Available for any status once the upload succeeded.

### Extracted text (truncated)

```bash
curl http://localhost:8000/api/documents/1/content/
```

Only for `status: ready`. Text is capped at `DOCUMENT_CONTENT_MAX_CHARS` (default 120k).

```json
{
  "document": { "id": 1, "filename": "policy.md", "created_at": "..." },
  "content": "...",
  "truncated": false,
  "max_chars": 120000,
  "total_chars": 4523
}
```

---

## Search

```bash
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"refund policy","limit":10,"document_ids":[1,3]}'
```

| Field | Required | Description |
|-------|----------|-------------|
| `query` | yes | Search text (1–2000 chars) |
| `limit` | no | Max results (default `SEARCH_DEFAULT_LIMIT`, max 50) |
| `document_ids` | no | Restrict to these document IDs; omit or `[]` for all |

`min_score` is **server-side only** (`SEARCH_MIN_SCORE`, default 0.5). Not accepted as a request parameter.

```json
{
  "query": "refund policy",
  "min_score": 0.5,
  "limit": 10,
  "total_above_threshold": 2,
  "results": [
    {
      "score": 0.87,
      "text": "...",
      "document": { "id": 1, "filename": "policy.md", "created_at": "..." },
      "chunk_index": 2
    }
  ]
}
```

`total_above_threshold` counts matches above the threshold within the candidate pool (`limit × SEARCH_CANDIDATE_MULTIPLIER`), not the entire database.

---

## Chunk context

Surrounding passages for a search hit (default ±1 chunk):

```bash
curl http://localhost:8000/api/documents/1/chunks/2/context/
```

```json
{
  "document": { "id": 1, "filename": "policy.md", "created_at": "..." },
  "chunk_index": 2,
  "chunks": [
    { "chunk_index": 1, "text": "...", "is_match": false },
    { "chunk_index": 2, "text": "...", "is_match": true },
    { "chunk_index": 3, "text": "...", "is_match": false }
  ]
}
```

---

## Errors

Structured error body:

```json
{ "error": "File exceeds maximum size of 50 MB.", "code": "FILE_TOO_LARGE" }
```

Common codes: `FILE_TOO_LARGE`, `TOO_MANY_FILES`, `INVALID_EXTENSION`, `DOCUMENT_LIMIT_REACHED`, `EMPTY_QUERY`, `NOT_FOUND`, `FILE_MISSING`.

---

## Upload limits

| Limit | Default | Env var |
|-------|---------|---------|
| Max file size | 50 MB | `MAX_UPLOAD_SIZE_MB` |
| Max files per request | 10 | `MAX_FILES_PER_UPLOAD` |
| Max total documents | 100 | `MAX_TOTAL_DOCUMENTS` |
| Allowed extensions | txt, md, pdf, docx | `ALLOWED_EXTENSIONS` |

Also: magic-byte validation, filename sanitization.
