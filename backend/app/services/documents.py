from django.conf import settings

from app.models import Document
from app.services.parsers import extract_text_from_path, get_extension


def get_document_content(document_id: int) -> dict | None:
    document = Document.objects.filter(pk=document_id, status="ready").first()
    if document is None:
        return None

    extension = get_extension(document.filename)
    text = extract_text_from_path(document.file_path, extension)

    max_chars = settings.DOCUMENT_CONTENT_MAX_CHARS
    truncated = len(text) > max_chars
    content = text[:max_chars] if truncated else text

    return {
        "document": {
            "id": document.id,
            "filename": document.filename,
            "created_at": document.created_at.isoformat(),
        },
        "content": content,
        "truncated": truncated,
        "max_chars": max_chars,
        "total_chars": len(text),
    }
