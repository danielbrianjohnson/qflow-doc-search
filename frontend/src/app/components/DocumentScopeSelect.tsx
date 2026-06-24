"use client";

import { useEffect, useRef, useState } from "react";
import { Document } from "@/lib/api";

interface DocumentScopeSelectProps {
  documents: Document[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
}

export default function DocumentScopeSelect({
  documents,
  selectedIds,
  onChange,
}: DocumentScopeSelectProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const readyDocuments = documents.filter((doc) => doc.status === "ready");

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggleId = (id: number) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((x) => x !== id));
    } else {
      onChange([...selectedIds, id]);
    }
  };

  const summary =
    selectedIds.length === 0
      ? "All documents"
      : selectedIds.length === 1
        ? readyDocuments.find((d) => d.id === selectedIds[0])?.filename ?? "1 document"
        : `${selectedIds.length} documents selected`;

  return (
    <div className="space-y-1 relative" ref={containerRef}>
      <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
        Search in
      </label>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="w-full flex items-center justify-between rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-sm text-left focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <span className="truncate">{summary}</span>
        <span className="text-slate-400 ml-2">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="absolute z-20 mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-lg max-h-60 overflow-y-auto">
          <div className="flex items-center justify-between px-3 py-2 border-b border-slate-200 dark:border-slate-800">
            <span className="text-xs text-slate-500">Select one or more (empty = all)</span>
            {selectedIds.length > 0 && (
              <button
                type="button"
                onClick={() => onChange([])}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                Clear
              </button>
            )}
          </div>
          {readyDocuments.length === 0 ? (
            <p className="px-3 py-4 text-sm text-slate-500">No ready documents.</p>
          ) : (
            <ul className="py-1">
              {readyDocuments.map((doc) => (
                <li key={doc.id}>
                  <label className="flex items-center gap-2 px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(doc.id)}
                      onChange={() => toggleId(doc.id)}
                    />
                    <span className="text-sm truncate">{doc.filename}</span>
                  </label>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {selectedIds.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {selectedIds.map((id) => {
            const doc = readyDocuments.find((d) => d.id === id);
            if (!doc) return null;
            return (
              <span
                key={id}
                className="inline-flex items-center gap-1 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 px-2 py-0.5 text-xs"
              >
                {doc.filename}
                <button
                  type="button"
                  onClick={() => toggleId(id)}
                  className="hover:text-blue-600"
                  aria-label={`Remove ${doc.filename}`}
                >
                  ×
                </button>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
