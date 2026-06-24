import logging
import re
from dataclasses import dataclass

from django.conf import settings
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)

_tokenizer = None


def get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(settings.EMBEDDING_MODEL)
    return _tokenizer


@dataclass
class TextChunk:
    text: str
    token_count: int


def count_tokens(text: str) -> int:
    return len(get_tokenizer().encode(text, add_special_tokens=False))


def split_markdown(text: str) -> list[str]:
    sections = re.split(r"(?=^#{1,3}\s)", text, flags=re.MULTILINE)
    return [s.strip() for s in sections if s.strip()]


def split_plain_text(text: str) -> list[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    result = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if count_tokens(para) <= settings.CHUNK_SIZE_TOKENS:
            result.append(para)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            current = ""
            for sentence in sentences:
                candidate = f"{current} {sentence}".strip() if current else sentence
                if count_tokens(candidate) <= settings.CHUNK_SIZE_TOKENS:
                    current = candidate
                else:
                    if current:
                        result.append(current)
                    current = sentence
            if current:
                result.append(current)
    return result


def sub_chunk_section(section: str) -> list[str]:
    tokenizer = get_tokenizer()
    tokens = tokenizer.encode(section, add_special_tokens=False)
    if len(tokens) <= settings.CHUNK_SIZE_TOKENS:
        return [section]

    chunks = []
    stride = settings.CHUNK_SIZE_TOKENS - settings.CHUNK_OVERLAP_TOKENS
    start = 0
    while start < len(tokens):
        end = min(start + settings.CHUNK_SIZE_TOKENS, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True).strip()
        if chunk_text:
            chunks.append(chunk_text)
        if end >= len(tokens):
            break
        start += stride
    return chunks


def chunk_text(text: str, extension: str) -> list[TextChunk]:
    text = text.strip()
    if not text:
        return []

    if extension == "md":
        sections = split_markdown(text)
    else:
        sections = split_plain_text(text)

    raw_chunks: list[str] = []
    for section in sections:
        raw_chunks.extend(sub_chunk_section(section))

      # Deduplicate adjacent identical chunks from overlap
    deduped: list[str] = []
    for chunk in raw_chunks:
        if not deduped or deduped[-1] != chunk:
            deduped.append(chunk)

    return [
        TextChunk(text=chunk, token_count=count_tokens(chunk))
        for chunk in deduped
        if chunk.strip()
    ]
