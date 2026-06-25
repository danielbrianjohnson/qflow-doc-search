# Embeddings

## Why run the model locally?

This service embeds documents and queries **on the same machine** using [sentence-transformers](https://www.sbert.net/), not a hosted API (OpenAI, Cohere, etc.).

### Reasons

| Concern | Local approach |
|---------|----------------|
| **No API keys** | Evaluators and developers run `docker compose up` with zero external setup. No secrets in `.env`. |
| **Cost** | No per-token billing. Embedding cost is fixed compute time on your hardware. |
| **Privacy** | Uploaded document text never leaves the deployment. Important for internal policies, HR docs, or customer data in real deployments. |
| **Determinism** | Same model version + same input → same vector. Easier to debug search quality and reproduce results. |
| **Offline / air-gapped** | Works without internet after the Docker image is built (model weights are baked in or cached on first run). |

Trade-off: you own CPU/GPU capacity and model upgrades. For an assessment and small-to-medium corpora, that trade-off is acceptable.

---

## Model: `BAAI/bge-small-en-v1.5`

| Property | Value |
|----------|-------|
| Dimensions | 384 |
| Size | ~130 MB |
| Runtime | CPU (PyTorch CPU wheel in Docker) |
| Library | sentence-transformers |

**Why this model?**

- Strong retrieval quality for English at small-model scale (better than older MiniLM variants in benchmarks).
- 384 dimensions match pgvector column size and keep index memory reasonable.
- Runs comfortably on CPU for demo workloads; no GPU required.
- Well-supported retrieval prefix for queries (see below).

Configurable via `EMBEDDING_MODEL` if you want to experiment.

---

## How encoding works

### Document chunks

Passage text is encoded as-is, in batches of 32, with **normalized** embeddings (unit length) so cosine similarity equals dot product.

```python
# backend/app/services/embeddings.py
embeddings = model.encode(
    texts,
    batch_size=32,
    normalize_embeddings=True,
)
```

### Search queries

bge models expect a retrieval prefix on queries:

```
Represent this sentence for searching relevant passages: {query}
```

Passages are not prefixed — only the query. This asymmetry is intentional and improves retrieval for bge.

---

## When the model loads

The model is loaded **lazily** on first use:

- Health check (`GET /api/health/`) triggers warmup and reports `embedding_model: ready | loading`
- Celery worker warms up on `worker_process_init` so the first document doesn’t pay full load time

The Docker image pre-installs CPU PyTorch and downloads model weights at build time where possible, so cold start is mostly memory mapping, not a full pip install.

---

## Alternatives considered

| Option | Why not (for this project) |
|--------|------------------------------|
| OpenAI `text-embedding-3-small` | Requires API key, network, ongoing cost, data leaves the box |
| Larger bge / e5 models | Better quality but slower on CPU; small model is enough for assessment scale |
| ONNX / quantized runtime | Good production optimization; added build complexity for marginal gain here |

For production at higher scale: GPU workers, model quantization, or a managed embedding API with strict data-processing agreements.
