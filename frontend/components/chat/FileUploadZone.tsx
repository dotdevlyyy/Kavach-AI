"use client";

import { useState, useRef } from "react";
import { UploadCloud, File, X } from "lucide-react";

interface FileUploadZoneProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
}

export function FileUploadZone({ files, onFilesChange }: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files);
      onFilesChange([...files, ...newFiles]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      onFilesChange([...files, ...newFiles]);
    }
  };

  const removeFile = (indexToRemove: number) => {
    onFilesChange(files.filter((_, idx) => idx !== indexToRemove));
  };

  return (
    <div className="w-full mb-3">
      {/* Dropped Files Preview */}
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {files.map((file, idx) => (
            <div key={idx} className="flex items-center gap-2 bg-sidebar-accent border border-border px-3 py-1.5 rounded-md text-xs">
              <File className="w-3 h-3 text-primary" />
              <span className="truncate max-w-[150px] text-foreground">{file.name}</span>
              <button 
                onClick={() => removeFile(idx)}
                className="text-muted-foreground hover:text-destructive ml-1 rounded focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                aria-label={`Remove ${file.name}`}
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Drag & Drop Target */}
      <div 
        className={`border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center transition-colors ${
          isDragging ? "border-primary bg-primary/5" : "border-border bg-sidebar/50 hover:bg-sidebar-accent/50"
        }`}
        role="button"
        tabIndex={0}
        aria-label="Choose files to attach"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            fileInputRef.current?.click();
          }
        }}
      >
        <UploadCloud className={`w-8 h-8 mb-2 ${isDragging ? "text-primary" : "text-muted-foreground"}`} />
        <p className="text-sm text-muted-foreground text-center">
          <span className="font-medium text-foreground">Click to upload</span> or drag and drop<br/>
          <span className="text-xs">PDF, DOCX, XLSX, text, code, and images (Max 20 MB per file)</span>
        </p>
        <input
          type="file" 
          multiple 
          ref={fileInputRef} 
          className="hidden" 
          accept=".pdf,.docx,.xlsx,.csv,.txt,.md,.json,.png,.jpg,.jpeg,.gif,.bmp,.webp,.tif,.tiff,.py,.js,.ts,.tsx,.jsx,.html,.css,.cpp,.go,.rs,.java,.sh"
          onChange={handleFileChange}
        />
      </div>
    </div>
  );
}
