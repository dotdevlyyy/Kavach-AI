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
      
      <div className="relative flex flex-col bg-white border border-gray-200 rounded-xl p-3 shadow-sm focus-within:border-gray-300 transition-colors h-[140px]">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question that will route to a sub-agent..."
          className="flex-1 w-full bg-transparent border-none focus:ring-0 resize-none py-1 px-1 text-sm text-gray-800 placeholder:text-gray-500"
        />

        <div className="flex justify-between items-center mt-auto">
          <button 
            onClick={() => setShowUploader(!showUploader)}
            className={`p-1.5 rounded-lg transition-colors ${showUploader || files.length > 0 ? "text-primary" : "text-gray-400 hover:bg-gray-100"}`}
            title="Attach files"
          >
            <Paperclip className="w-4 h-4" />
            {files.length > 0 && (
              <span className="absolute bottom-4 left-6 w-3 h-3 rounded-full bg-primary text-[8px] font-bold text-white flex items-center justify-center">
                {files.length}
              </span>
            )}
          </button>

          <button 
            onClick={handleSubmit}
            disabled={(!input.trim() && files.length === 0) || isStreaming}
            className="p-1.5 rounded-lg bg-gray-500 text-white disabled:opacity-30 disabled:bg-gray-300 hover:bg-gray-600 transition-colors"
          >
            {isStreaming ? (
              <div className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14"></path>
                <path d="m12 5 7 7-7 7"></path>
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
