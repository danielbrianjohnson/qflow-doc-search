export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Document {
  id: number;
  filename: string;
  content_type: string;
  file_size: number;
  status: "queued" | "processing" | "ready" | "failed";
  error_message: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface SearchResult {
  score: number;
  text: string;
  document: {
    id: number;
    filename: string;
    created_at: string;
  };
  chunk_index: number;
}

export interface SearchResponse {
  query: string;
  min_score: number;
  limit: number;
  total_above_threshold: number;
  results: SearchResult[];
}

export interface ContextChunk {
  chunk_index: number;
  text: string;
  is_match: boolean;
}

export interface ChunkContext {
  document: {
    id: number;
    filename: string;
    created_at: string;
  };
  chunk_index: number;
  chunks: ContextChunk[];
}

export interface DocumentContentResponse {
  document: {
    id: number;
    filename: string;
    created_at: string;
  };
  content: string;
  truncated: boolean;
  max_chars: number;
  total_chars: number;
}

export interface ApiError {
  error: string;
  code: string;
}

export async function fetchDocuments(): Promise<Document[]> {
  const res = await fetch(`${API_URL}/api/documents/`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to fetch documents");
  }
  const data = await res.json();
  return data.results ?? data;
}

export async function uploadDocuments(files: File[]): Promise<Document[]> {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));

  const res = await fetch(`${API_URL}/api/documents/`, {
    method: "POST",
    body: form,
  });

  const data = await res.json();
  if (!res.ok) {
    const err = data as ApiError;
    throw new Error(err.error || "Upload failed");
  }
  return data.documents;
}

export async function deleteDocument(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/api/documents/${id}/`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error("Failed to delete document");
  }
}

export function getDocumentDownloadUrl(id: number): string {
  return `${API_URL}/api/documents/${id}/download/`;
}

export async function searchDocuments(
  query: string,
  options?: {
    documentIds?: number[];
    limit?: number;
  }
): Promise<SearchResponse> {
  const res = await fetch(`${API_URL}/api/search/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      limit: options?.limit ?? 10,
      ...(options?.documentIds && options.documentIds.length > 0
        ? { document_ids: options.documentIds }
        : {}),
    }),
  });

  const data = await res.json();
  if (!res.ok) {
    const err = data as ApiError;
    throw new Error(err.error || "Search failed");
  }
  return data as SearchResponse;
}

export async function fetchChunkContext(
  documentId: number,
  chunkIndex: number
): Promise<ChunkContext> {
  const res = await fetch(
    `${API_URL}/api/documents/${documentId}/chunks/${chunkIndex}/context/`,
    { cache: "no-store" }
  );
  const data = await res.json();
  if (!res.ok) {
    const err = data as ApiError;
    throw new Error(err.error || "Failed to load chunk context");
  }
  return data as ChunkContext;
}

export async function fetchDocumentContent(
  documentId: number
): Promise<DocumentContentResponse> {
  const res = await fetch(`${API_URL}/api/documents/${documentId}/content/`, {
    cache: "no-store",
  });
  const data = await res.json();
  if (!res.ok) {
    const err = data as ApiError;
    throw new Error(err.error || "Failed to load document content");
  }
  return data as DocumentContentResponse;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function truncateText(text: string, maxLength = 220): string {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength).trim()}…`;
}
