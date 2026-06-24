import django.db.models.deletion
from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_enable_pgvector"),
    ]

    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("filename", models.CharField(max_length=512)),
                ("content_type", models.CharField(blank=True, max_length=128)),
                ("file_size", models.PositiveIntegerField(default=0)),
                ("file_path", models.CharField(max_length=1024)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("queued", "Queued"),
                            ("processing", "Processing"),
                            ("ready", "Ready"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="queued",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True, null=True)),
                ("chunk_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DocumentChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chunk_index", models.PositiveIntegerField()),
                ("text", models.TextField()),
                ("embedding", pgvector.django.VectorField(dimensions=384)),
                ("token_count", models.PositiveIntegerField(default=0)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunks",
                        to="app.document",
                    ),
                ),
            ],
            options={
                "ordering": ["document_id", "chunk_index"],
            },
        ),
        migrations.AddConstraint(
            model_name="documentchunk",
            constraint=models.UniqueConstraint(
                fields=("document", "chunk_index"),
                name="unique_chunk_per_document",
            ),
        ),
        migrations.AddIndex(
            model_name="documentchunk",
            index=pgvector.django.HnswIndex(
                ef_construction=64,
                fields=["embedding"],
                m=16,
                name="chunk_embedding_hnsw_idx",
                opclasses=["vector_cosine_ops"],
            ),
        ),
    ]
