"use client";

import { FileText, Table, Download } from "lucide-react";

interface DeliverableCardProps {
  id: string;
  filename: string;
  type: "docx" | "xlsx";
  sizeBytes?: number;
}

export function DeliverableCard({ id, filename, type, sizeBytes }: DeliverableCardProps) {
  const isWord = type === "docx";
  const Icon = isWord ? FileText : Table;
  
  // Format bytes to KB/MB
  const formatSize = (bytes?: number) => {
    if (!bytes) return "Unknown size";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const handleDownload = () => {
    // In Phase 5, this will be wired to actual API download
    // e.g. window.open(`/api/files/download/${id}`)
    alert(`Downloading ${filename} (ID: ${id})`);
  };

  return (
    <div className="flex items-center justify-between p-3 my-2 bg-white shadow-sm border border-gray-200 rounded-lg max-w-sm hover:border-gray-300 transition-colors">
      <div className="flex items-center gap-3 overflow-hidden">
        <div className={`p-2 rounded-md shrink-0 ${isWord ? "bg-blue-50 text-blue-600" : "bg-emerald-50 text-emerald-600"}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="flex flex-col min-w-0">
          <span className="text-sm font-medium text-gray-800 truncate">{filename}</span>
          <span className="text-xs text-gray-500">{formatSize(sizeBytes)} • Ready</span>
        </div>
      </div>
      
      <button 
        onClick={handleDownload}
        className="p-2 shrink-0 rounded-md text-gray-400 hover:bg-gray-100 hover:text-gray-900 transition-colors ml-2"
        title="Download File"
      >
        <Download className="w-4 h-4" />
      </button>
    </div>
  );
}
