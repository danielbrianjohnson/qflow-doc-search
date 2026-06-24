from django.conf import settings
from pgvector.django import CosineDistance

from app.models import DocumentChunk
from app.services.embeddings import get_embedding_service


def search_chunks(
    query: str,
    document_ids: list[int] | None = None,
    limit: int = 10,
) -> dict:
    embedding_service = get_embedding_service()
    query_vector = embedding_service.encode_query(query)
    threshold = settings.SEARCH_MIN_SCORE

    queryset = DocumentChunk.objects.select_related("document").filter(
        document__status="ready",
    )

    if document_ids:
        queryset = queryset.filter(document_id__in=document_ids)

    candidate_limit = min(
        limit * settings.SEARCH_CANDIDATE_MULTIPLIER,
        settings.SEARCH_MAX_LIMIT * settings.SEARCH_CANDIDATE_MULTIPLIER,
    )

    candidates = (
        queryset.annotate(distance=CosineDistance("embedding", query_vector))
        .order_by("distance")[:candidate_limit]
    )

    above_threshold = []
    for chunk in candidates:
        similarity = max(0.0, 1.0 - float(chunk.distance))
        if similarity < threshold:
            continue
        above_threshold.append(
            {
                "score": round(similarity, 4),
                "text": chunk.text,
                "document": {
                    "id": chunk.document_id,
                    "filename": chunk.document.filename,
                    "created_at": chunk.document.created_at.isoformat(),
                },
                "chunk_index": chunk.chunk_index,
            }
        )

    results = above_threshold[:limit]

    return {
        "query": query,
        "min_score": threshold,
        "limit": limit,
        "total_above_threshold": len(above_threshold),
        "results": results,
    }
