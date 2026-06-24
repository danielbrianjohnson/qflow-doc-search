"use client";

import { useState } from "react";
import ResultDetailModal from "./ResultDetailModal";
import { SearchResponse, SearchResult, formatDateTime, truncateText } from "@/lib/api";

interface SearchPanelProps {
  onSearch: (query: string) => Promise<void>;
  searchResponse: SearchResponse | null;
  lastQuery: string;
  searching: boolean;
  scopeLabel: string;
}

export default function SearchPanel({
  onSearch,
  searchResponse,
  lastQuery,
  searching,
  scopeLabel,
}: SearchPanelProps) {
  const [query, setQuery] = useState("");
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    await onSearch(query.trim());
  };

  const results = searchResponse?.results ?? [];

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about your documents…"
          className="flex-1 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={searching || !query.trim()}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {searching ? "Searching…" : "Search"}
        </button>
      </form>

      <p className="text-xs text-slate-500 dark:text-slate-400">
        Scope: {scopeLabel}
        {searchResponse && (
          <>
            {" "}
            · Min relevance: {(searchResponse.min_score * 100).toFixed(0)}%
          </>
        )}
      </p>

      {searchResponse && !searching && (
        <p className="text-sm text-slate-600 dark:text-slate-300">
          {searchResponse.total_above_threshold === 0 ? (
            <>No results above {(searchResponse.min_score * 100).toFixed(0)}% relevance. Try rephrasing your query.</>
          ) : (
            <>
              {searchResponse.total_above_threshold} result
              {searchResponse.total_above_threshold !== 1 ? "s" : ""} above threshold
              {searchResponse.total_above_threshold > results.length &&
                ` (showing top ${results.length})`}
            </>
          )}
        </p>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((result, i) => (
            <button
              key={`${result.document.id}-${result.chunk_index}-${i}`}
              type="button"
              onClick={() => setSelectedResult(result)}
              className="w-full text-left rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 hover:border-blue-400 dark:hover:border-blue-600 transition-colors"
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-sm font-medium text-blue-600 dark:text-blue-400 truncate">
                  {result.document.filename}
                </span>
                <span className="text-xs text-slate-500 shrink-0">
                  {(result.score * 100).toFixed(1)}% match
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">
                Uploaded {formatDateTime(result.document.created_at)}
              </p>
              <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                {truncateText(result.text)}
              </p>
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">View full passage →</p>
            </button>
          ))}
        </div>
      )}

      <ResultDetailModal
        result={selectedResult}
        query={lastQuery}
        onClose={() => setSelectedResult(null)}
      />
    </div>
  );
}
