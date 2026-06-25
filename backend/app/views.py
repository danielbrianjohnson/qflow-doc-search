from pathlib import Path

from django.db import connection
from django.http import FileResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Document
from app.serializers import DocumentSerializer, DocumentUploadSerializer, SearchSerializer
from app.services.chunks import get_chunk_context
from app.services.documents import get_document_content
from app.services.embeddings import get_embedding_service
from app.services.search import search_chunks
from app.tasks import process_document
from app.throttling import SearchRateThrottle, UploadRateThrottle


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        db_ok = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_ok = True
        except Exception:
            db_ok = False

        embedding_service = get_embedding_service()
        try:
            embedding_service.warmup()
            embedding_ready = embedding_service.is_ready
        except Exception:
            embedding_ready = False

        overall = db_ok and embedding_ready
        payload = {
            "status": "ok" if overall else "degraded",
            "database": "ok" if db_ok else "error",
            "embedding_model": "ready" if embedding_ready else "loading",
        }
        http_status = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=http_status)


class DocumentListCreateView(generics.ListCreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    throttle_classes = [UploadRateThrottle]

    def get_throttles(self):
        if self.request.method == "POST":
            return [UploadRateThrottle()]
        return []

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DocumentUploadSerializer
        return DocumentSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = DocumentSerializer(page or queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist("files")
        if not files:
            single = request.FILES.get("file")
            if single:
                files = [single]

        serializer = DocumentUploadSerializer(data={"files": files})
        serializer.is_valid(raise_exception=True)
        documents = serializer.save()

        for document in documents:
            process_document.delay(document.id)

        output = DocumentSerializer(documents, many=True)
        return Response({"documents": output.data}, status=status.HTTP_202_ACCEPTED)


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def perform_destroy(self, instance):
        file_path = Path(instance.file_path)
        if file_path.exists():
            file_path.unlink()
        instance.delete()


class SearchView(APIView):
    throttle_classes = [SearchRateThrottle]

    def post(self, request):
        serializer = SearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        payload = search_chunks(
            query=data["query"],
            document_ids=data.get("document_ids"),
            limit=data["limit"],
        )

        return Response(payload)


class DocumentChunkContextView(APIView):
    def get(self, request, pk: int, chunk_index: int):
        context = get_chunk_context(document_id=pk, chunk_index=chunk_index, window=1)
        if context is None:
            return Response(
                {"error": "Document not found or not ready.", "code": "NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(context)


class DocumentContentView(APIView):
    def get(self, request, pk: int):
        payload = get_document_content(document_id=pk)
        if payload is None:
            return Response(
                {"error": "Document not found or not ready.", "code": "NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(payload)


class DocumentDownloadView(APIView):
    def get(self, request, pk: int):
        document = Document.objects.filter(pk=pk).first()
        if document is None:
            return Response(
                {"error": "Document not found.", "code": "NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        file_path = Path(document.file_path)
        if not file_path.is_file():
            return Response(
                {"error": "Original file is no longer available.", "code": "FILE_MISSING"},
                status=status.HTTP_404_NOT_FOUND,
            )

        response = FileResponse(
            file_path.open("rb"),
            as_attachment=True,
            filename=document.filename,
        )
        if document.content_type:
            response["Content-Type"] = document.content_type
        return response
