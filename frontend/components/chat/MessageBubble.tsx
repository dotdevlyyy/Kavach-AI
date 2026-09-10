"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { ModelBadge } from "./ModelBadge";
import { toast } from "sonner";
import {
  MessageBubble as AgentsMessageBubble,
  MessageBubbleContent,
} from "@/components/beui/components/agents/message-bubble";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  model?: "llama3.2:1b" | "qwen2.5-coder:1.5b" | "qwen2.5vl:3b";
}

export function MessageBubble({ role, content, model }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <AgentsMessageBubble
      align={isUser ? "end" : "start"}
      variant={isUser ? "tint" : "ghost"}
      className="mb-8"
    >
      <MessageBubbleContent className={isUser ? undefined : "max-w-[85%]"}>
        {/* Header for assistant messages showing which model answered */}
        {!isUser && model && (
          <div className="mb-3 flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-sidebar-accent flex items-center justify-center">
              <span className="text-[10px] font-bold text-sidebar-foreground">AI</span>
            </div>
            <ModelBadge model={model} />
          </div>
        )}

        {/* Content using ReactMarkdown */}
        <div className="prose max-w-none text-sm text-foreground dark:prose-invert">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ inline, className, children }: { inline?: boolean; className?: string; children?: React.ReactNode }) {
                const match = /language-([\w+-]+)/.exec(className || "");
                return !inline ? (
                  <div className="not-prose my-4 max-w-full overflow-hidden rounded-md border border-border">
                    <div className="bg-sidebar px-4 py-1 text-xs text-muted-foreground border-b border-border flex justify-between">
                      <span>{match?.[1] || "code"}</span>
                      <button 
                        onClick={() => {
                          navigator.clipboard.writeText(String(children).replace(/\n$/, ""));
                          toast.success("Code copied to clipboard", {
                            description: "You can now paste this directly into your IDE.",
                          });
                        }}
                        className="hover:text-primary transition-colors cursor-pointer rounded px-1 focus-visible:outline-2 focus-visible:outline-primary"
                        aria-label="Copy code"
                      >
                        Copy
                      </button>
                    </div>
                    <SyntaxHighlighter
                      language={match?.[1] || "text"}
                      style={oneDark}
                      PreTag="div"
                      customStyle={{ margin: 0, padding: "1rem", background: "transparent", fontSize: "0.875rem", lineHeight: "1.5", overflowX: "auto" }}
                      codeTagProps={{ className: "!bg-transparent !p-0" }}
                    >
                      {String(children).replace(/\n$/, "")}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code className="bg-sidebar-accent px-1.5 py-0.5 rounded text-xs text-primary font-mono">
                    {children}
                  </code>
                );
              }
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </MessageBubbleContent>
    </AgentsMessageBubble>
  );
}
