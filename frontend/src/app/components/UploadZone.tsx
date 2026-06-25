"use client";

import { useCallback, useRef, useState } from "react";

interface UploadZoneProps {
  onUpload: (files: File[]) => Promise<void>;
  disabled?: boolean;
}

export default function UploadZone({ onUpload, disabled }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);

  const handleFiles = useCallback((fileList: FileList | null) => {
    if (!fileList || fileList.length === 0 || disabled || uploading) return;
    setPendingFiles(Array.from(fileList));
  }, [disabled, uploading]);

  const startUpload = useCallback(async () => {
    if (pendingFiles.length === 0) return;
    setUploading(true);
    try {
      await onUpload(pendingFiles);
      setPendingFiles([]);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }, [onUpload, pendingFiles]);

  return (
    <div
      className={`rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
        dragging
          ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
          : "border-slate-300 dark:border-slate-700"
      } ${disabled || uploading ? "opacity-60 cursor-not-allowed" : "cursor-pointer"}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => !disabled && !uploading && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".txt,.md,.pdf,.docx"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <div className="space-y-2">
        <p className="text-lg font-medium">
          {uploading
            ? "Uploading…"
            : pendingFiles.length > 0
              ? `${pendingFiles.length} file(s) selected`
              : "Drop files here or click to browse"}
        </p>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          .txt, .md, .pdf, .docx — up to 10 files, 50 MB each
        </p>
        {pendingFiles.length > 0 && !uploading && (
          <div className="flex items-center justify-center gap-2 pt-1">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                startUpload();
              }}
              className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              Start upload
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setPendingFiles([]);
                if (inputRef.current) inputRef.current.value = "";
              }}
              className="rounded-md border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-sm hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              Clear
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
