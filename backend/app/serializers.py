import uuid
from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from app.exceptions import ServiceError
from app.models import Document
from app.services.parsers import get_extension, sanitize_filename, validate_file


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "filename",
            "content_type",
            "file_size",
            "status",
            "error_message",
            "chunk_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class DocumentUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False,
        write_only=True,
    )

    def validate_files(self, files):
        if len(files) > settings.MAX_FILES_PER_UPLOAD:
            raise serializers.ValidationError(
                f"Too many files. Maximum {settings.MAX_FILES_PER_UPLOAD} per upload.",
                code="TOO_MANY_FILES",
            )

        current_count = Document.objects.count()
        if current_count + len(files) > settings.MAX_TOTAL_DOCUMENTS:
            raise serializers.ValidationError(
                f"Corpus limit of {settings.MAX_TOTAL_DOCUMENTS} documents would be exceeded.",
                code="CORPUS_LIMIT_REACHED",
            )

        validated = []
        for uploaded in files:
            try:
                safe_name = sanitize_filename(uploaded.name)
                validate_file(uploaded, safe_name)
            except ServiceError as exc:
                detail = exc.detail if isinstance(exc.detail, dict) else {"error": str(exc.detail)}
                raise serializers.ValidationError(
                    detail.get("error", "Invalid file"),
                    code=detail.get("code", "INVALID_FILE"),
                ) from exc
            validated.append(
                {
                    "file": uploaded,
                    "filename": safe_name,
                    "extension": get_extension(safe_name),
                }
            )
        return validated

    def create(self, validated_data):
        documents = []
        upload_dir = Path(settings.MEDIA_ROOT)
        upload_dir.mkdir(parents=True, exist_ok=True)

        for item in validated_data["files"]:
            uploaded = item["file"]
            filename = item["filename"]
            unique_name = f"{uuid.uuid4().hex}_{filename}"
            dest = upload_dir / unique_name

            with dest.open("wb") as out:
                for chunk in uploaded.chunks():
                    out.write(chunk)

            document = Document.objects.create(
                filename=filename,
                content_type=uploaded.content_type or "",
                file_size=uploaded.size,
                file_path=str(dest),
                status="queued",
            )
            documents.append(document)

        return documents


class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(min_length=1, max_length=2000)
    limit = serializers.IntegerField(
        required=False,
        default=settings.SEARCH_DEFAULT_LIMIT,
        min_value=1,
        max_value=settings.SEARCH_MAX_LIMIT,
    )
    document_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )

    def validate_query(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Query cannot be empty.", code="EMPTY_QUERY")
        return cleaned

    def validate_document_ids(self, value):
        if not value:
            return None
        existing = set(
            Document.objects.filter(id__in=value, status="ready").values_list("id", flat=True)
        )
        missing = sorted(set(value) - existing)
        if missing:
            raise serializers.ValidationError(
                f"Documents not found or not ready: {missing}",
                code="INVALID_DOCUMENT_IDS",
            )
        return value
