from app.models import Document, DocumentChunk


def get_chunk_context(document_id: int, chunk_index: int, window: int = 1) -> dict:
    document = Document.objects.filter(pk=document_id, status="ready").first()
    if document is None:
        return None

    chunks = DocumentChunk.objects.filter(
        document_id=document_id,
        chunk_index__gte=chunk_index - window,
        chunk_index__lte=chunk_index + window,
    ).order_by("chunk_index")

    return {
        "document": {
            "id": document.id,
            "filename": document.filename,
            "created_at": document.created_at.isoformat(),
        },
        "chunk_index": chunk_index,
        "chunks": [
            {
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "is_match": chunk.chunk_index == chunk_index,
            }
            for chunk in chunks
        ],
    }
