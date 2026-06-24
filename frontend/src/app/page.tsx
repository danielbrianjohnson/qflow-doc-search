"use client";

import { useCallback, useEffect, useState } from "react";
import DocumentScopeSelect from "./components/DocumentScopeSelect";
import RecentUploads from "./components/RecentUploads";
import SearchPanel from "./components/SearchPanel";
import UploadZone from "./components/UploadZone";
import {
  Document,
  SearchResponse,
  deleteDocument,
  fetchDocuments,
  searchDocuments,
  uploadDocuments,
} from "@/lib/api";

export default function HomePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [scopeDocumentIds, setScopeDocumentIds] = useState<number[]>([]);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [lastQuery, setLastQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadDocuments = useCallback(async () => {
    try {
      const docs = await fetchDocuments();
      setDocuments(docs);
      setScopeDocumentIds((prev) =>
        prev.filter((id) => docs.some((d) => d.id === id && d.status === "ready"))
      );
      return docs;
    } catch {
      setError("Could not load documents. Is the API running?");
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const hasPendingDocuments = documents.some(
    (doc) => doc.status === "queued" || doc.status === "processing"
  );

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    if (!hasPendingDocuments) return;

    const interval = setInterval(() => {
      loadDocuments();
    }, 3000);

    return () => clearInterval(interval);
  }, [hasPendingDocuments, loadDocuments]);

  const handleUpload = async (files: File[]) => {
    setError(null);
    setInfo(null);
    try {
      const existingNames = new Set(documents.map((d) => d.filename.toLowerCase()));
      const duplicateNames = files
        .map((f) => f.name)
        .filter((name) => existingNames.has(name.toLowerCase()));

      await uploadDocuments(files);
      await loadDocuments();

      if (duplicateNames.length > 0) {
        setInfo(
          `Uploaded successfully. Note: "${duplicateNames.join('", "')}" already existed — both copies are searchable.`
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    }
  };

  const handleDelete = async (id: number) => {
    setError(null);
    try {
      await deleteDocument(id);
      setScopeDocumentIds((prev) => prev.filter((x) => x !== id));
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  const handleSearch = async (query: string) => {
    setError(null);
    setInfo(null);
    setSearching(true);
    setLastQuery(query);
    try {
      const response = await searchDocuments(query, {
        documentIds: scopeDocumentIds.length > 0 ? scopeDocumentIds : undefined,
      });
      setSearchResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setSearchResponse(null);
    } finally {
      setSearching(false);
    }
  };

  const readyById = new Map(
    documents.filter((d) => d.status === "ready").map((d) => [d.id, d.filename])
  );

  const scopeLabel =
    scopeDocumentIds.length === 0
      ? "All documents"
      : scopeDocumentIds.length === 1
        ? readyById.get(scopeDocumentIds[0]) ?? "1 document"
        : `${scopeDocumentIds.length} documents`;

  return (
    <main className="mx-auto max-w-4xl px-4 py-10 space-y-8">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Document Search</h1>
        <p className="text-slate-600 dark:text-slate-400">
          Upload documents and search by meaning using local vector embeddings.
        </p>
      </header>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950 px-4 py-3 text-sm text-red-800 dark:text-red-200">
          {error}
        </div>
      )}

      {info && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950 px-4 py-3 text-sm text-amber-900 dark:text-amber-100">
          {info}
        </div>
      )}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Upload</h2>
        <UploadZone onUpload={handleUpload} />
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Search</h2>
        <DocumentScopeSelect
          documents={documents}
          selectedIds={scopeDocumentIds}
          onChange={setScopeDocumentIds}
        />
        <SearchPanel
          onSearch={handleSearch}
          searchResponse={searchResponse}
          lastQuery={lastQuery}
          searching={searching}
          scopeLabel={scopeLabel}
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Recent uploads</h2>
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4">
          <RecentUploads documents={documents} onDelete={handleDelete} loading={loading} />
        </div>
        {documents.length > 8 && (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Showing 8 most recent. Manage all documents in Django admin.
          </p>
        )}
      </section>
    </main>
  );
}
