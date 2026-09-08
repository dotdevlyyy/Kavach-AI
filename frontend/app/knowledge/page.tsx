"use client";

import { UploadCloud, FileText } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export default function KnowledgeBasePage() {
  return (
    <div className="p-8">
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
                Add new Standard Operating Procedures (SOPs), P&IDs, or Inspection Reports to the local vector database.
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
                Ingest & Embed
              </button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
      
      <div className="p-6 bg-card border border-border rounded-xl flex items-start gap-4">
        <FileText className="w-8 h-8 text-primary shrink-0" />
        <div>
          <h3 className="text-lg font-semibold text-foreground">Indexed Documents</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Documents listed here have been chunked, embedded, and are currently available to the RAG Agent.
          </p>
          <div className="mt-4 p-4 border border-dashed border-border rounded-lg bg-sidebar-accent/30 flex items-center justify-center text-sm text-muted-foreground italic">
            // @Pritam: Wire up the GET /api/knowledge/documents list here...
          </div>
        </div>
      </div>
    </div>
  );
}
