import logging
import uuid
from pathlib import Path

from django.conf import settings
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

    try:
        extension = get_extension(document.filename)
        text = extract_text_from_path(document.file_path, extension)
        chunks = chunk_text(text, extension)

        if not chunks:
            raise ValueError("No text content found after extraction.")

        embedding_service = get_embedding_service()
        texts = [c.text for c in chunks]
        embeddings = embedding_service.encode(texts)

        with transaction.atomic():
            DocumentChunk.objects.filter(document=document).delete()
            chunk_objects = [
                DocumentChunk(
                    document=document,
                    chunk_index=index,
                    text=chunk.text,
                    embedding=embedding,
                    token_count=chunk.token_count,
                )
                for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
            ]
            DocumentChunk.objects.bulk_create(chunk_objects, batch_size=100)
            document.status = DocumentStatus.READY
            document.chunk_count = len(chunk_objects)
            document.error_message = None
            document.save(update_fields=["status", "chunk_count", "error_message", "updated_at"])

        logger.info("Processed document %s (%d chunks)", document_id, len(chunks))

    except Exception as exc:
        logger.exception("Failed to process document %s", document_id)
        document.status = DocumentStatus.FAILED
        document.error_message = str(exc)
        document.save(update_fields=["status", "error_message", "updated_at"])
        raise


def save_uploaded_file(file_obj, filename: str) -> str:
    upload_dir = Path(settings.MEDIA_ROOT)
    upload_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    dest = upload_dir / unique_name
    with dest.open("wb") as out:
        for chunk in file_obj.chunks():
            out.write(chunk)
    return str(dest)
