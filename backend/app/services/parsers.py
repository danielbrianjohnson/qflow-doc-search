import io
import logging
import re
from pathlib import Path

import filetype
from django.conf import settings
from docx import Document as DocxDocument
from pypdf import PdfReader

from app.exceptions import ServiceError

logger = logging.getLogger(__name__)

EXTENSION_CONTENT_TYPES = {
    "txt": {"text/plain"},
    "md": {"text/plain", "text/markdown", "text/x-markdown"},
    "pdf": {"application/pdf"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    },
}


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[^\w.\- ]", "_", name)
    name = name.strip().strip(".")
    if not name:
        raise ServiceError("Invalid filename.", code="INVALID_FILENAME")
    return name[:512]


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def validate_file(file_obj, filename: str) -> str:
    ext = get_extension(filename)
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise ServiceError(
            f"Unsupported file type '.{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            code="UNSUPPORTED_FILE_TYPE",
        )

    if file_obj.size == 0:
        raise ServiceError("File is empty.", code="EMPTY_FILE")

    if file_obj.size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise ServiceError(
            f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
            code="FILE_TOO_LARGE",
        )

    head = file_obj.read(261)
    file_obj.seek(0)
    kind = filetype.guess(head)
    detected = kind.extension if kind else None

    if ext == "txt" or ext == "md":
        try:
            sample = head.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ServiceError("File is not valid UTF-8 text.", code="INVALID_TEXT_FILE") from exc
        if ext == "md" and detected and detected not in ("txt", "md") and detected != ext:
            # Allow text-like markdown without strict magic match
            pass
        return ext

    if ext == "pdf":
        if detected != "pdf":
            raise ServiceError("File content does not match PDF extension.", code="INVALID_FILE_CONTENT")
        return ext

    if ext == "docx":
        if detected not in ("docx", "zip"):
            raise ServiceError("File content does not match DOCX extension.", code="INVALID_FILE_CONTENT")
        return ext

    return ext


def extract_text_from_bytes(content: bytes, extension: str) -> str:
    if extension in ("txt", "md"):
        return content.decode("utf-8")

    if extension == "pdf":
        return extract_pdf_text(io.BytesIO(content))

    if extension == "docx":
        return extract_docx_text(io.BytesIO(content))

    raise ServiceError(f"No parser for extension '.{extension}'", code="UNSUPPORTED_FILE_TYPE")


def extract_text_from_path(file_path: str, extension: str) -> str:
    path = Path(file_path)
    if extension in ("txt", "md"):
        return path.read_text(encoding="utf-8")

    if extension == "pdf":
        with path.open("rb") as f:
            return extract_pdf_text(f)

    if extension == "docx":
        with path.open("rb") as f:
            return extract_docx_text(f)

    raise ServiceError(f"No parser for extension '.{extension}'", code="UNSUPPORTED_FILE_TYPE")


def extract_pdf_text(file_obj) -> str:
    reader = PdfReader(file_obj)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())
    if not pages:
        raise ServiceError("Could not extract text from PDF.", code="EXTRACTION_FAILED")
    return "\n\n".join(pages)


def extract_docx_text(file_obj) -> str:
    doc = DocxDocument(file_obj)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    if not paragraphs:
        raise ServiceError("Could not extract text from DOCX.", code="EXTRACTION_FAILED")
    return "\n\n".join(paragraphs)
