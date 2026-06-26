import logging

from django.db import transaction

from app.models import Document, DocumentChunk, DocumentStatus
from app.services.chunking import chunk_text
from app.services.embeddings import get_embedding_service
from app.services.parsers import extract_text_from_path, get_extension

logger = logging.getLogger(__name__)


def process_document(document_id: int) -> None:
    document = Document.objects.get(pk=document_id)

    document.status = DocumentStatus.PROCESSING
    document.error_message = None
    document.save(update_fields=["status", "error_message", "updated_at"])

    extension = get_extension(document.filename)
    text = extract_text_from_path(document.file_path, extension)
    chunks = chunk_text(text, extension)

    if not chunks:
        raise ValueError("No text content found after chunking.")

    embedding_service = get_embedding_service()
    embedding_service.warmup()
    texts = [c.text for c in chunks]
    vectors = embedding_service.encode(texts)

    with transaction.atomic():
        DocumentChunk.objects.filter(document=document).delete()
        chunk_objects = [
            DocumentChunk(
                document=document,
                chunk_index=index,
                text=chunk.text,
                embedding=vector,
                token_count=chunk.token_count,
            )
            for index, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]
        DocumentChunk.objects.bulk_create(chunk_objects, batch_size=100)
        document.chunk_count = len(chunk_objects)
        document.status = DocumentStatus.READY
        document.error_message = None
        document.save(update_fields=["chunk_count", "status", "error_message", "updated_at"])

    logger.info("Document %s processed with %s chunks.", document_id, document.chunk_count)


def mark_document_failed(document_id: int, error_message: str) -> None:
    document = Document.objects.filter(pk=document_id).first()
    if document is None:
        return
    document.status = DocumentStatus.FAILED
    document.error_message = error_message[:2000]
    document.save(update_fields=["status", "error_message", "updated_at"])
