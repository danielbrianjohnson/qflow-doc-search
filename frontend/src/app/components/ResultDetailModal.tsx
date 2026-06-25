"use client";

import { ReactNode, useEffect, useState } from "react";
import {
  ChunkContext,
  DocumentContentResponse,
  SearchResult,
  fetchChunkContext,
  fetchDocumentContent,
  formatDateTime,
} from "@/lib/api";

interface ResultDetailModalProps {
  result: SearchResult | null;
  query: string;
  onClose: () => void;
}

const STOP_WORDS = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "by",
  "for",
  "from",
  "in",
  "is",
  "it",
  "of",
  "on",
  "or",
  "that",
  "the",
  "to",
  "was",
  "were",
  "with",
]);

function highlightText(text: string, query: string, highlight: boolean): ReactNode[] {
  if (!highlight) {
    return [text];
  }

  const normalizedQuery = query.trim();
  const phrase = normalizedQuery.length >= 4 ? normalizedQuery : "";

  const terms = normalizedQuery
    .toLowerCase()
    .split(/\s+/)
    .map((t) => t.trim())
    .filter((t) => t.length >= 3 && !STOP_WORDS.has(t));

  if (!phrase && terms.length === 0) {
    return [text];
  }

  const patternParts = [];
  if (phrase) {
    patternParts.push(escapeRegex(phrase));
  }
  patternParts.push(...terms.map(escapeRegex));
  const pattern = new RegExp(`(${Array.from(new Set(patternParts)).join("|")})`, "gi");
  const parts = text.split(pattern);

  return parts.map((part, i) => {
    const lower = part.toLowerCase();
    const isPhraseMatch = phrase.length > 0 && lower === phrase.toLowerCase();
    const isTermMatch = terms.some((term) => lower === term.toLowerCase());
    const isMatch = isPhraseMatch || isTermMatch;
    if (isMatch) {
      return (
        <mark
          key={i}
          className="bg-yellow-200 text-slate-900 dark:bg-yellow-500/40 dark:text-yellow-50 rounded px-0.5"
        >
          {part}
        </mark>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export default function ResultDetailModal({ result, query, onClose }: ResultDetailModalProps) {
  const [context, setContext] = useState<ChunkContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);
  const bodyMaxHeightClass = "max-h-[calc(85vh-96px)]";
  const [showFullDoc, setShowFullDoc] = useState(false);
  const [fullDocLoading, setFullDocLoading] = useState(false);
  const [fullDocError, setFullDocError] = useState<string | null>(null);
  const [fullDoc, setFullDoc] = useState<DocumentContentResponse | null>(null);

  useEffect(() => {
    if (!result) {
      setContext(null);
      setContextError(null);
      setShowFullDoc(false);
      setFullDoc(null);
      setFullDocError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setContextError(null);

    fetchChunkContext(result.document.id, result.chunk_index)
      .then((data) => {
        if (!cancelled) setContext(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setContextError(err instanceof Error ? err.message : "Could not load context");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [result]);

  if (!result) return null;

  const chunks = context?.chunks ?? [
    {
      chunk_index: result.chunk_index,
      text: result.text,
      is_match: true,
    },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="result-modal-title"
    >
      <div
        className="w-full max-w-2xl rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 dark:border-slate-800 px-5 py-4">
          <div className="min-w-0">
            <h3 id="result-modal-title" className="font-semibold truncate">
              {result.document.filename}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Uploaded {formatDateTime(result.document.created_at)} · Match chunk{" "}
              {result.chunk_index + 1} · {(result.score * 100).toFixed(1)}% relevance
            </p>
          </div>
          <button
            onClick={onClose}
            className="shrink-0 rounded-lg px-2 py-1 text-sm text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className={`overflow-y-auto px-5 py-4 space-y-4 ${bodyMaxHeightClass}`}>
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              View surrounding chunks, or open full document text.
            </p>
            <button
              type="button"
              onClick={async () => {
                const next = !showFullDoc;
                setShowFullDoc(next);
                if (!next || fullDoc || fullDocLoading) return;
                setFullDocLoading(true);
                setFullDocError(null);
                try {
                  const payload = await fetchDocumentContent(result.document.id);
                  setFullDoc(payload);
                } catch (err) {
                  setFullDocError(
                    err instanceof Error ? err.message : "Could not load full document"
                  );
                } finally {
                  setFullDocLoading(false);
                }
              }}
              className="text-xs rounded-md border border-slate-300 dark:border-slate-700 px-2 py-1 hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              {showFullDoc ? "Hide full document" : "View full document"}
            </button>
          </div>

          {loading && (
            <p className="text-sm text-slate-500">Loading surrounding context…</p>
          )}
          {contextError && (
            <p className="text-sm text-amber-700 dark:text-amber-300">{contextError}</p>
          )}

          {!loading &&
            chunks.map((chunk) => (
              <div
                key={chunk.chunk_index}
                className={
                  chunk.is_match
                    ? "rounded-lg border border-blue-300 dark:border-blue-700 bg-blue-50/50 dark:bg-blue-950/30 p-3"
                    : "rounded-lg border border-slate-200 dark:border-slate-800 p-3 opacity-80"
                }
              >
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2">
                  {chunk.is_match ? "Matching passage" : `Context · chunk ${chunk.chunk_index + 1}`}
                </p>
                <div className="text-sm leading-relaxed whitespace-pre-wrap">
                  {highlightText(chunk.text, query, chunk.is_match)}
                </div>
              </div>
            ))}

          {showFullDoc && (
            <div className="rounded-lg border border-slate-200 dark:border-slate-800 p-3">
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2">
                Full document (text extraction)
              </p>
              {fullDocLoading && (
                <p className="text-sm text-slate-500">Loading full document…</p>
              )}
              {fullDocError && (
                <p className="text-sm text-amber-700 dark:text-amber-300">{fullDocError}</p>
              )}
              {!fullDocLoading && fullDoc && (
                <>
                  {fullDoc.truncated && (
                    <p className="text-xs text-amber-700 dark:text-amber-300 mb-2">
                      Showing first {fullDoc.max_chars.toLocaleString()} of{" "}
                      {fullDoc.total_chars.toLocaleString()} characters.
                    </p>
                  )}
                  <div className="text-sm leading-relaxed whitespace-pre-wrap">
                    {fullDoc.content}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
