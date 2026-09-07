"use client";

import { useState, useRef } from "react";
import { UploadCloud, File, X } from "lucide-react";

interface FileUploadZoneProps {
  onFilesSelected: (files: File[]) => void;
}

export function FileUploadZone({ onFilesSelected }: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
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
      setSelectedFiles((prev) => [...prev, ...newFiles]);
      onFilesSelected(newFiles);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...newFiles]);
      onFilesSelected(newFiles);
    }
  };

  const removeFile = (indexToRemove: number) => {
    setSelectedFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  return (
    <div className="w-full mb-3">
      {/* Dropped Files Preview */}
      {selectedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {selectedFiles.map((file, idx) => (
            <div key={idx} className="flex items-center gap-2 bg-sidebar-accent border border-border px-3 py-1.5 rounded-md text-xs">
              <File className="w-3 h-3 text-primary" />
              <span className="truncate max-w-[150px] text-foreground">{file.name}</span>
              <button 
                onClick={() => removeFile(idx)}
                className="text-muted-foreground hover:text-destructive ml-1"
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
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <UploadCloud className={`w-8 h-8 mb-2 ${isDragging ? "text-primary" : "text-muted-foreground"}`} />
        <p className="text-sm text-muted-foreground text-center">
          <span className="font-medium text-foreground">Click to upload</span> or drag and drop<br/>
          <span className="text-xs">PDF, DOCX, XLSX, PNG, JPG (Max 50MB)</span>
        </p>
        <input 
          type="file" 
          multiple 
          ref={fileInputRef} 
          className="hidden" 
          onChange={handleFileChange}
        />
      </div>
    </div>
  );
}
