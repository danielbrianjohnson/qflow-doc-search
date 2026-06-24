import logging

from celery import shared_task
from django.db import transaction

from app.models import Document, DocumentChunk
from app.services.chunking import chunk_text
from app.services.embeddings import get_embedding_service
from app.services.parsers import extract_text_from_path, get_extension

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def process_document(self, document_id: int):
    try:
        document = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        logger.warning("Document %s not found.", document_id)
        return

    document.status = "processing"
    document.error_message = None
    document.save(update_fields=["status", "error_message", "updated_at"])

    try:
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
            document.status = "ready"
            document.error_message = None
            document.save(update_fields=["chunk_count", "status", "error_message", "updated_at"])

        logger.info("Document %s processed with %s chunks.", document_id, document.chunk_count)

    except Exception as exc:
        logger.exception("Failed to process document %s", document_id)
        document.status = "failed"
        document.error_message = str(exc)[:2000]
        document.save(update_fields=["status", "error_message", "updated_at"])
        raise self.retry(exc=exc) if self.request.retries < self.max_retries else exc
