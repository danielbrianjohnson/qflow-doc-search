# ADR 001: Document status updates (polling vs push)

**Status:** Accepted (polling, conditional)  
**Date:** 2026-06-24  
**Context:** Document embedding runs asynchronously in Celery. The frontend must reflect status transitions (`queued` → `processing` → `ready` | `failed`) without requiring a full page reload.

---

## Decision

Use **conditional HTTP polling** on `GET /api/documents/`:

- Poll every **3 seconds** while any document has status `queued` or `processing`
- Stop polling when all documents are `ready` or `failed`
- Fetch once on page load and immediately after upload/delete

This is implemented in `frontend/src/app/page.tsx`.

---

## Alternatives considered

### 1. Unconditional polling (initial implementation)

Poll every 3s regardless of document state.

| Pros | Cons |
|------|------|
| Simplest code | Wastes requests when idle |
| Always fresh list | Noisy in network tab / server logs |

**Rejected** in favor of conditional polling.

---

### 2. Conditional polling (current)

Only poll when work is in flight.

| Pros | Cons |
|------|------|
| Simple — no backend changes | Up to 3s latency before UI shows `ready` |
| Stops when idle | Not truly real-time |
| Works with existing REST API | |

**Accepted** for this assessment.

---

### 3. Server-Sent Events (SSE)

Backend streams status events: `event: status\ndata: {"id": 1, "status": "ready"}`.

| Pros | Cons |
|------|------|
| Push updates, near real-time | Requires new endpoint + connection handling |
| One-way (server → client) — sufficient for status | Django dev server / gunicorn config for long-lived connections |
| Simpler than WebSockets for this use case | Reconnect logic on disconnect |

**Good next step** if sub-second status updates matter and you want to avoid WebSocket complexity.

Implementation sketch:

1. `GET /api/documents/{id}/events/` — Django `StreamingHttpResponse`
2. Celery task publishes to Redis pub/sub on status change
3. SSE view subscribes and forwards events to the client
4. Frontend `EventSource` updates document row in state

---

### 4. WebSockets

Persistent bidirectional channel (e.g. Django Channels, Socket.IO).

| Pros | Cons |
|------|------|
| Full duplex, real-time | Heavyweight for status-only updates |
| Good for collaborative UIs | Extra infra (ASGI server, channel layer, often Redis) |
| | More moving parts for evaluators to run |

**Overkill** for “refresh a status badge after background job completes.” Prefer SSE or polling first.

---

### 5. Celery result backend / job ID polling

Upload returns `task_id`; frontend polls `GET /api/tasks/{task_id}/`.

| Pros | Cons |
|------|------|
| Precise per-upload tracking | Extra endpoint; couples UI to Celery |
| No list polling | Harder for multi-document overview |

Viable for a job-centric API; we chose document-centric status on the `Document` model instead.

---

## Recommendation for production

| Scale / need | Approach |
|--------------|----------|
| Assessment, low traffic | **Conditional polling** ✅ |
| Faster updates, still simple | **SSE** |
| Chat, live collaboration | **WebSockets** |
| High fan-out, many concurrent uploads | SSE or WebSocket + Redis pub/sub |

---

## Related code

| Component | Path |
|-----------|------|
| Frontend polling | `frontend/src/app/page.tsx` |
| Upload API | `backend/app/views.py` → `DocumentListCreateView` |
| Background job | `backend/app/tasks.py` → `services/processing.py` |
| Status model | `backend/app/models.py` → `Document.status` |
