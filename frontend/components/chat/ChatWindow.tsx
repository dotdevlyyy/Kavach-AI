"use client";

import { useState } from "react";
import { Paperclip } from "lucide-react";
import { PromptInput } from "@/components/beui/components/agents/prompt-input";
import { Button } from "@/components/beui/components/motion/button";
import { FileUploadZone } from "./FileUploadZone";

interface ChatWindowProps {
  onSendMessage: (message: string, files: File[]) => Promise<boolean>;
  onCancel: () => void;
  isStreaming: boolean;
}

export function ChatWindow({ onSendMessage, onCancel, isStreaming }: ChatWindowProps) {
  const [input, setInput] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [showUploader, setShowUploader] = useState(false);
  const handleSubmit = async () => {
    if ((input.trim() || files.length > 0) && !isStreaming) {
      const draft = input;
      const attached = files;
      setInput("");
      setFiles([]);
      setShowUploader(false);
      const sent = await onSendMessage(draft, attached);
      if (sent) {
        return;
      }
      setInput(draft);
      setFiles(attached);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col gap-2">
      {showUploader && (
        <FileUploadZone files={files} onFilesChange={setFiles} />
      )}
      
      <PromptInput
        value={input}
        onValueChange={setInput}
        onSubmit={() => void handleSubmit()}
        loading={isStreaming}
        onStop={onCancel}
        placeholder="Ask Kavach AI to analyze, create, or execute..."
        leadingAction={
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label={showUploader ? "Close file attachment picker" : "Attach files"}
            onClick={() => setShowUploader((open) => !open)}
            className="relative"
          >
            <Paperclip className="size-4" />
            {files.length > 0 ? <span className="absolute -right-1 -top-1 grid size-3 place-items-center rounded-full bg-primary text-[8px] text-primary-foreground">{files.length}</span> : null}
          </Button>
        }
      />
    </div>
  );
}
