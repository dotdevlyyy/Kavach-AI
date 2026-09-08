"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { ModelBadge } from "./ModelBadge";
import { toast } from "sonner";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  model?: "llama3.2:1b" | "qwen2.5-coder:1.5b" | "qwen2.5vl:3b";
}

export function MessageBubble({ role, content, model }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} mb-6`}>
      <div className={`max-w-[80%] rounded-xl px-5 py-4 shadow-sm ${
        isUser 
          ? "bg-primary text-primary-foreground rounded-tr-sm" 
          : "bg-card border border-border text-card-foreground rounded-tl-sm"
      }`}>
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
        <div className="prose prose-invert max-w-none text-sm">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ node, inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || "");
                return !inline && match ? (
                  <div className="rounded-md overflow-hidden my-4 border border-border">
                    <div className="bg-sidebar px-4 py-1 text-xs text-muted-foreground border-b border-border flex justify-between">
                      <span>{match[1]}</span>
                      <button 
                        onClick={() => {
                          navigator.clipboard.writeText(String(children).replace(/\n$/, ""));
                          toast.success("Code copied to clipboard", {
                            description: "You can now paste this directly into your IDE.",
                          });
                        }}
                        className="hover:text-primary transition-colors cursor-pointer"
                      >
                        Copy
                      </button>
                    </div>
                    <SyntaxHighlighter
                      style={vscDarkPlus as any}
                      language={match[1]}
                      PreTag="div"
                      customStyle={{ margin: 0, borderRadius: 0 }}
                      {...props}
                    >
                      {String(children).replace(/\n$/, "")}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code className="bg-sidebar-accent px-1.5 py-0.5 rounded text-xs text-primary font-mono" {...props}>
                    {children}
                  </code>
                );
              }
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
