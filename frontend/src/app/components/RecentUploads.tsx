"use client";

import { Document, formatDateTime, formatFileSize, getDocumentDownloadUrl } from "@/lib/api";

interface RecentUploadsProps {
  documents: Document[];
  onDelete: (id: number) => Promise<void>;
  loading?: boolean;
}

const statusStyles: Record<Document["status"], string> = {
  queued: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  processing: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  ready: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  failed: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
};

const RECENT_LIMIT = 8;

export default function RecentUploads({ documents, onDelete, loading }: RecentUploadsProps) {
  const recent = documents.slice(0, RECENT_LIMIT);

  if (loading) {
    return <p className="text-sm text-slate-500 py-3 text-center">Loading…</p>;
  }

  if (recent.length === 0) {
    return (
      <p className="text-sm text-slate-500 dark:text-slate-400 py-3 text-center">
        No uploads yet.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-slate-200 dark:divide-slate-800">
      {recent.map((doc) => (
        <li key={doc.id} className="flex items-start justify-between gap-3 py-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-sm truncate">{doc.filename}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full capitalize ${statusStyles[doc.status]}`}
              >
                {doc.status}
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {formatDateTime(doc.created_at)} · {formatFileSize(doc.file_size)}
              {doc.status === "ready" && ` · ${doc.chunk_count} chunks`}
              {doc.status === "failed" && doc.error_message && ` · ${doc.error_message}`}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <a
              href={getDocumentDownloadUrl(doc.id)}
              download={doc.filename}
              className="text-xs text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
            >
              Download
            </a>
            <button
              onClick={() => {
                const ok = window.confirm(
                  `Delete "${doc.filename}"? This removes stored chunks and embeddings too.`
                );
                if (ok) {
                  onDelete(doc.id);
                }
              }}
              className="text-xs text-red-600 hover:text-red-800 dark:text-red-400"
            >
              Delete
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
