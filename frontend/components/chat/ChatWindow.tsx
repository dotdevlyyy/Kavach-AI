"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Paperclip } from "lucide-react";
import { FileUploadZone } from "./FileUploadZone";

interface ChatWindowProps {
  onSendMessage: (message: string, files: File[]) => void;
  isStreaming: boolean;
}

export function ChatWindow({ onSendMessage, isStreaming }: ChatWindowProps) {
  const [input, setInput] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [showUploader, setShowUploader] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if ((input.trim() || files.length > 0) && !isStreaming) {
      onSendMessage(input, files);
      setInput("");
      setFiles([]);
      setShowUploader(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col gap-2">
      {showUploader && (
        <FileUploadZone onFilesSelected={(newFiles) => setFiles(prev => [...prev, ...newFiles])} />
      )}
      
      <div className="relative flex items-end gap-2 bg-card border border-border rounded-xl p-2 shadow-sm focus-within:ring-1 focus-within:ring-primary focus-within:border-primary transition-all">
        <button 
          onClick={() => setShowUploader(!showUploader)}
          className={`p-2 rounded-lg transition-colors ${showUploader || files.length > 0 ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-sidebar-accent"}`}
          title="Attach files"
        >
          <Paperclip className="w-5 h-5" />
          {files.length > 0 && (
            <span className="absolute -top-1 -left-1 w-4 h-4 rounded-full bg-primary text-[10px] font-bold text-primary-foreground flex items-center justify-center">
              {files.length}
            </span>
          )}
        </button>

        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Kavach AI to analyze a report, write code, or execute a task..."
          className="flex-1 max-h-[200px] bg-transparent border-none focus:ring-0 resize-none py-2 px-1 text-sm text-foreground placeholder:text-muted-foreground"
          rows={1}
        />

        <button 
          onClick={handleSubmit}
          disabled={(!input.trim() && files.length === 0) || isStreaming}
          className="p-2 rounded-lg bg-primary text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
      <div className="text-center text-[10px] text-muted-foreground">
        Kavach AI can make mistakes. Always verify critical MRPL outputs.
      </div>
    </div>
  );
}
