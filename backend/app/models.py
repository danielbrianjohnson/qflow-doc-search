from django.db import models
from pgvector.django import HnswIndex, VectorField


class DocumentStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    PROCESSING = "processing", "Processing"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class Document(models.Model):
    filename = models.CharField(max_length=512)
    content_type = models.CharField(max_length=128, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    file_path = models.CharField(max_length=1024)
    status = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.QUEUED,
        db_index=True,
    )
    error_message = models.TextField(blank=True, null=True)
    chunk_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.filename} ({self.status})"


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    embedding = VectorField(dimensions=384)
    token_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["document_id", "chunk_index"]
        indexes = [
            HnswIndex(
                name="chunk_embedding_hnsw_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "chunk_index"],
                name="unique_chunk_per_document",
            ),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.filename}"
