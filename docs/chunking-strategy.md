# Chunking strategy

Chunking splits extracted document text into passages small enough to embed accurately, but large enough to preserve meaning. Implementation: `backend/app/services/chunking.py`.

---

## Goals

1. **Fit the model’s context** — embeddings degrade when text is truncated silently or when a single vector must represent unrelated topics.
2. **Preserve structure** — markdown headers and paragraphs should not be split mid-thought when avoidable.
3. **Improve retrieval** — search returns a *chunk*; it should be a coherent snippet a user can read.
4. **Bound overlap** — neighboring chunks should share enough context that a sentence spanning a boundary still appears in full in at least one chunk.

---

## Parameters

| Setting | Default | Env var |
|---------|---------|---------|
| Target chunk size | 512 tokens | `CHUNK_SIZE_TOKENS` |
| Overlap | 64 tokens | `CHUNK_OVERLAP_TOKENS` |

Token counts use the **same tokenizer as the embedding model** (`AutoTokenizer.from_pretrained(EMBEDDING_MODEL)`), not character or word counts. That keeps chunk boundaries aligned with what the model actually sees.

**Effective stride** = `512 - 64 = 448` tokens between chunk starts when sliding a long section.

---

## Why 512 tokens?

- Common RAG default (~400–512 tokens). Long enough for a policy paragraph or code comment block; short enough that one embedding ≈ one topic.
- bge-small handles passages up to 512 tokens without truncation for typical English text.
- Smaller chunks (128–256) → more rows, more index size, more fragmented search results.
- Larger chunks (1024+) → one vector averages multiple ideas; relevance scores become muddier.

512 is a practical default for general business documents (policies, reports, notes). Tune per domain if you know average section length.

---

## Why 64-token overlap?

When a section exceeds 512 tokens, the splitter slides a window with 64-token overlap:

```
[-------- 512 tokens --------]
              [-------- 512 tokens --------]
```

Overlap reduces “lost in the gap” problems: a sentence or definition that straddles a hard cut may still appear complete in an adjacent chunk. 64 tokens (~1–2 sentences) is a light overlap — enough for boundary coverage without storing near-duplicate chunks across the whole corpus.

Adjacent identical chunks from overlap are deduplicated before storage.

---

## Format-aware splitting

Chunking is **not** a single “split every N characters” pass.

### Markdown (`.md`)

1. Split on level 1–3 headers (`#`, `##`, `###`) so sections stay grouped.
2. If a section still exceeds 512 tokens, apply sliding token windows with overlap.

Headers often introduce a new topic; respecting them keeps each chunk semantically focused.

### Plain text, PDF, DOCX (`.txt`, `.pdf`, `.docx`)

1. Split on blank lines → paragraphs.
2. Paragraphs under 512 tokens are kept whole.
3. Long paragraphs are split on sentence boundaries (`.!?` followed by space).
4. If a section still exceeds 512 tokens, apply sliding token windows with overlap.

Sentence-level splitting avoids cutting mid-sentence when a paragraph is only slightly over the limit.

---

## Chunk count

There is no fixed “number of chunks per document.” Count depends on:

- Extracted text length
- Structure (many short sections vs one long wall of text)
- How often sliding windows are needed

The `Document.chunk_count` field is set after processing and shown in the UI when status is `ready`.

---

## Why not LangChain / fixed character splits?

- **Tokenizer alignment** — character-based 1000-char chunks don’t match model token limits; 1000 chars can be 200 or 800 tokens depending on content.
- **Format awareness** — generic recursive splitters don’t treat markdown headers as first-class boundaries.
- **Simplicity** — ~100 lines of explicit logic, no extra abstraction layer, easy to read in an assessment review.

---

## Tuning guide

| Symptom | Try |
|---------|-----|
| Results are too fragmented, missing context | Increase `CHUNK_SIZE_TOKENS` (e.g. 768) or overlap (e.g. 128) |
| Results mix unrelated topics in one hit | Decrease chunk size (e.g. 384) or improve header/paragraph splitting |
| Very long PDFs, slow indexing | Expected — more chunks = more embeddings; scale workers |
| Code or tables break badly | Add format-specific splitters (future work) |

---

## Related code

| Piece | Path |
|-------|------|
| Chunking logic | `backend/app/services/chunking.py` |
| Called from worker | `backend/app/tasks.py` → `process_document` |
| Stored as | `DocumentChunk.text`, `token_count`, `embedding` |
