"use client";

import { useEffect, useState } from "react";
import { UploadCloud, FileText } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface DocumentInfo {
  id: string;
  filename: string;
  file_type: string; // will be displayed uppercase
  created_at: string;
}

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${apiBase}/api/knowledge/documents`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      // Expected shape: { documents: DocumentInfo[] }
      setDocuments(data.documents ?? []);
    } catch (e: any) {
      setError(e?.message ?? "Unable to fetch documents");
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-foreground">Knowledge Base Manager</h1>
        <Dialog>
          <DialogTrigger className="px-4 py-2 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2">
            <UploadCloud className="w-5 h-5" />
            Upload SOP Document
          </DialogTrigger>
          <DialogContent className="sm:max-w-md border-border bg-card">
            <DialogHeader>
              <DialogTitle className="text-foreground">Upload Refinery Document</DialogTitle>
              <DialogDescription className="text-muted-foreground">
                Add new Standard Operating Procedures (SOPs), P&amp;IDs, or Inspection Reports to the local vector database.
              </DialogDescription>
            </DialogHeader>
            <div className="flex items-center justify-center w-full">
              <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-48 border-2 border-border border-dashed rounded-xl cursor-pointer bg-sidebar-accent/50 hover:bg-sidebar-accent transition-colors">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <UploadCloud className="w-10 h-10 mb-3 text-muted-foreground" />
                  <p className="mb-2 text-sm text-foreground"><span className="font-semibold">Click to upload</span> or drag and drop</p>
                  <p className="text-xs text-muted-foreground">PDF, DOCX, TXT, or PNG (MAX. 20MB)</p>
                </div>
                <input id="dropzone-file" type="file" className="hidden" />
              </label>
            </div>
            <div className="flex justify-end mt-4">
              <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors w-full sm:w-auto">
                Ingest &amp; Embed
              </button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Document list section */}
      {loading ? (
        <div className="grid grid-cols-1 gap-4">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="p-4 bg-card border border-border rounded-xl animate-pulse h-24" />
          ))}
        </div>
      ) : error ? (
        <div className="p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded-xl">
          <p className="font-medium">Error loading documents: {error}</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="p-4 bg-card border border-border rounded-xl text-muted-foreground">
          No indexed documents found. Upload documents using the manager above.
        </div>
      ) : (
        <div className="space-y-4">
          {documents.map((doc) => (
            <div key={doc.id} className="p-4 bg-card border border-border rounded-xl flex items-center gap-4">
              <FileText className="w-6 h-6 text-primary shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">{doc.filename}</p>
                <p className="text-xs text-muted-foreground">
                  {doc.file_type?.toUpperCase() || "UNKNOWN"} — {new Date(doc.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
