from django.contrib import admin

from app.models import Document, DocumentChunk


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    fields = ("chunk_index", "token_count", "text")
    readonly_fields = ("chunk_index", "token_count", "text")
    can_delete = False
    max_num = 20


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "filename", "status", "chunk_count", "file_size", "created_at")
    list_filter = ("status", "content_type")
    search_fields = ("filename",)
    readonly_fields = ("created_at", "updated_at", "chunk_count", "file_path")
    inlines = [DocumentChunkInline]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("id", "document", "chunk_index", "token_count")
    list_filter = ("document",)
    search_fields = ("text", "document__filename")
    readonly_fields = ("document", "chunk_index", "text", "token_count")
