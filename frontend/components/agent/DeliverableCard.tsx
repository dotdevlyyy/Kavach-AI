"use client";

import { FileText, Table, Download } from "lucide-react";

interface DeliverableCardProps {
  id: string;
  filename: string;
  type: string;
  sizeBytes?: number;
}

export function DeliverableCard({ id, filename, type, sizeBytes }: DeliverableCardProps) {
  const isWord = type === "docx";
  const isPdf = type === "pdf";
  const Icon = isPdf || isWord ? FileText : Table;
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const downloadUrl = `${apiBase}/api/files/download/${id}`;

  const formatSize = (bytes?: number) => {
    if (!bytes) return "Unknown size";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex items-center justify-between p-3 my-2 bg-card border border-border rounded max-w-sm hover:border-primary/50 transition-colors">
      <div className="flex items-center gap-3 overflow-hidden min-w-0">
        <div className={`p-2 rounded shrink-0 ${isPdf ? "bg-amber-500/10 text-amber-500" : (isWord ? "bg-primary/10 text-primary" : "bg-emerald-500/10 text-emerald-500")}`}>
          <Icon className="w-6 h-6" aria-hidden="true" />
        </div>
        <div className="flex flex-col min-w-0">
          <span className="text-sm font-medium text-foreground truncate">{filename}</span>
          <span className="text-xs text-muted-foreground">{formatSize(sizeBytes)} · Ready</span>
        </div>
      </div>
      <a
        href={downloadUrl}
        download
        className="p-2 shrink-0 rounded text-muted-foreground hover:bg-muted hover:text-foreground transition-colors ml-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        aria-label={`Download ${filename}`}
      >
        <Download className="w-4 h-4" aria-hidden="true" />
      </a>
    </div>
  );
}
