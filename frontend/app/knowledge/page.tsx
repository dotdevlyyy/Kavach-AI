"use client";

import { useEffect, useState } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { AgentDocScanner } from "@/components/agents-ui/agent-doc-scanner";

interface DocumentInfo {
  id: string;
  filename: string;
  file_type: string;
  created_at: string;
  chunk_count?: number;
}

function apiError(response: Response, fallback: string) {
  return response.json()
    .then((body: { detail?: string }) => body.detail || fallback)
    .catch(() => fallback);
}

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const [ingestMessage, setIngestMessage] = useState<string | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${apiBase}/api/knowledge/documents`);
      if (!res.ok) throw new Error(await apiError(res, `HTTP ${res.status}`));
      const data = await res.json() as { documents?: DocumentInfo[] };
      setDocuments(data.documents ?? []);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to fetch documents");
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleIngest = async () => {
    if (!selectedFile || isIndexing) return;
    setIsIndexing(true);
    setIngestMessage(null);
    setIngestError(null);
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const formData = new FormData();
      formData.append("files", selectedFile);
      const upload = await fetch(`${apiBase}/api/files/upload`, { method: "POST", body: formData });
      if (!upload.ok) throw new Error(await apiError(upload, `Upload failed: HTTP ${upload.status}`));
      const uploaded = await upload.json() as { files?: { id: string }[] };
      const fileId = uploaded.files?.[0]?.id;
      if (!fileId) throw new Error("Upload failed: backend returned no file ID");

      const index = await fetch(`${apiBase}/api/knowledge/index`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: fileId }),
      });
      if (!index.ok) throw new Error(await apiError(index, `Indexing failed: HTTP ${index.status}`));
      const result = await index.json() as { filename: string; chunks_created: number };
      setIngestMessage(`Indexed ${result.filename}: ${result.chunks_created} chunks created.`);
      setSelectedFile(null);
      await fetchDocuments();
    } catch (cause) {
      setIngestError(cause instanceof Error ? cause.message : "Document indexing failed");
    } finally {
      setIsIndexing(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Knowledge Base Manager</h1>
          <p className="text-sm text-muted-foreground mt-1">Upload local SOPs and index searchable evidence.</p>
        </div>
        <Dialog>
          <DialogTrigger className="px-4 py-2 bg-primary text-primary-foreground font-medium rounded hover:bg-primary/90 transition-colors flex items-center gap-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
            <UploadCloud className="w-5 h-5" aria-hidden="true" />
            Upload SOP Document
          </DialogTrigger>
          <DialogContent className="sm:max-w-md border-border bg-card rounded">
            <DialogHeader>
              <DialogTitle className="text-foreground">Upload Refinery Document</DialogTitle>
              <DialogDescription className="text-muted-foreground">
                PDF, DOCX, CSV, TXT, Markdown, or images. Maximum 20 MB per file.
              </DialogDescription>
            </DialogHeader>
            <AgentDocScanner
              document={selectedFile ? { name: selectedFile.name, type: (selectedFile.name.split(".").pop()?.toLowerCase() === "pdf" ? "pdf" : selectedFile.name.split(".").pop()?.toLowerCase() === "csv" ? "csv" : selectedFile.name.split(".").pop()?.toLowerCase() === "xlsx" ? "xlsx" : selectedFile.name.split(".").pop()?.toLowerCase() === "docx" ? "docx" : "txt"), size: selectedFile.size } : undefined}
              isProcessing={isIndexing}
              onFileUpload={setSelectedFile}
              showBottomActions={false}
            />
            {ingestError && <p className="mt-3 text-sm text-destructive" role="alert"><AlertCircle className="inline w-4 h-4 mr-1" aria-hidden="true" />{ingestError}</p>}
            {ingestMessage && <p className="mt-3 text-sm text-emerald-600" role="status"><CheckCircle2 className="inline w-4 h-4 mr-1" aria-hidden="true" />{ingestMessage}</p>}
            <div className="flex justify-end mt-4">
              <button onClick={handleIngest} disabled={!selectedFile || isIndexing} className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors w-full sm:w-auto disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
                {isIndexing ? "Indexing…" : "Ingest & Embed"}
              </button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-4" aria-label="Loading documents">
          {[...Array(2)].map((_, i) => <div key={i} className="p-4 bg-card border border-border rounded animate-pulse h-24" />)}
        </div>
      ) : error ? (
        <div className="p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded" role="alert">Error loading documents: {error}</div>
      ) : documents.length === 0 ? (
        <div className="p-8 bg-card border border-border rounded text-center text-muted-foreground">No indexed documents found. Upload one to begin.</div>
      ) : (
        <div className="space-y-2" aria-live="polite">
          {documents.map((doc) => (
            <div key={doc.id} className="p-4 bg-card border border-border rounded flex items-center gap-4">
              <FileText className="w-6 h-6 text-primary shrink-0" aria-hidden="true" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{doc.filename}</p>
                <p className="text-xs text-muted-foreground">{doc.file_type?.toUpperCase() || "UNKNOWN"} · {new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(doc.created_at))}</p>
              </div>
              {typeof doc.chunk_count === "number" && <span className="text-xs text-muted-foreground">{doc.chunk_count} chunks</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
