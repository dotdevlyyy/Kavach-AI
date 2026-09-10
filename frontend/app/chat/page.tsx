"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { AgentActivity, AgentStep } from "@/components/agent/AgentStepCard";
import { DeliverableCard } from "@/components/agent/DeliverableCard";
import { consumeSSEStream, uploadFiles, StreamEvent } from "@/lib/StreamConsumer";
import { ChatMessage, useChatStore } from "@/lib/store";
import { v4 as uuidv4 } from 'uuid';
import { GitBranch, FileCode2 } from "lucide-react";
import { ChatWorkflowModal } from "@/components/chat/ChatWorkflowModal";
import { ChatArtifactsModal } from "@/components/chat/ChatArtifactsModal";
import { toast } from "sonner";
import { LoadingState } from "@/components/beautiful-ui/loading-state";

const outputFilename = (filename: string) => filename.replace(/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}_/i, "");

export default function ChatPage() {
  const activeChatId = useChatStore((state) => state.activeChatId);
  const chats = useChatStore((state) => state.chats);
  const hasHydrated = useChatStore((state) => state.hasHydrated);
  const addMessage = useChatStore((state) => state.addMessage);
  const updateMessage = useChatStore((state) => state.updateMessage);
  const createChat = useChatStore((state) => state.createChat);

  // Initialize a chat if none exists
  useEffect(() => {
    if (hasHydrated && chats.length === 0) {
      createChat();
    }
  }, [chats.length, createChat, hasHydrated]);

  const activeChat = chats.find(c => c.id === activeChatId) || chats[0];
  const activeChatMessages = activeChat?.messages;
  const messages = useMemo(() => activeChatMessages || [], [activeChatMessages]);

  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStartedAt, setStreamStartedAt] = useState<number | null>(null);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [isWorkflowModalOpen, setIsWorkflowModalOpen] = useState(false);
  const [isArtifactsModalOpen, setIsArtifactsModalOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamControllerRef = useRef<AbortController | null>(null);
  const streamTaskIdRef = useRef<string | null>(null);

  const allArtifacts = messages.flatMap(m => {
    const userFiles = (m.attachedFiles || []).map(f => ({ id: f.id, name: f.name, type: f.type, origin: "user" as const }));
    const agentFiles = (m.deliverables || []).map(f => ({ id: f.id, name: f.filename, type: f.type, origin: "agent" as const }));
    return [...userFiles, ...agentFiles];
  });
  const hasArtifacts = allArtifacts.length > 0;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: isStreaming ? "auto" : "smooth" });
  }, [isStreaming, messages]);

  const handleSendMessage = async (message: string, files: File[]): Promise<boolean> => {
    if (!activeChatId) return false;
    const currentChatId = activeChatId;

    let fileIds: string[] = [];
    let attachedFilesData: { id: string; name: string; type: string }[] = [];
    if (files.length > 0) {
      try {
        fileIds = await uploadFiles(files);
      } catch (error) {
        toast.error("Upload failed", { description: error instanceof Error ? error.message : "Try again." });
        return false;
      }
      // Map the IDs back to the original files
      attachedFilesData = files.map((file, i) => ({
        id: fileIds[i] || uuidv4(),
        name: file.name,
        type: file.name.split('.').pop() || 'file'
      }));
    }

    const userMsgId = uuidv4();
    addMessage(currentChatId, {
      id: userMsgId,
      role: "user",
      content: message + (files.length > 0 ? `\n\n*[Attached ${files.length} files]*` : ""),
      attachedFiles: attachedFilesData
    });
    
    setStreamStartedAt(Date.now());
    setIsStreaming(true);
    const controller = new AbortController();
    streamControllerRef.current = controller;
    streamTaskIdRef.current = null;
    
    const assistantMsgId = uuidv4();
    setStreamingMessageId(assistantMsgId);
    addMessage(currentChatId, {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      steps: [],
      deliverables: []
    });

    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const agentKeywords = ["plan", "execute", "generate", "create", "make a", "build a", "pdf", "word doc", "excel", "spreadsheet", "report", "presentation", "ppt", "docx"];
    const isAgentTask = agentKeywords.some(kw => message.toLowerCase().includes(kw));
    const endpoint = isAgentTask ? `${apiBase}/api/agent/execute` : `${apiBase}/api/chat`;
    const payload = isAgentTask 
      ? { task_description: message, conversation_id: currentChatId, file_ids: fileIds, max_steps: 10 }
      : { message, conversation_id: currentChatId, file_ids: fileIds };

    await consumeSSEStream(endpoint, payload, (event: StreamEvent) => {
      if (event.type === "metadata" && typeof event.data.task_id === "string") {
        streamTaskIdRef.current = event.data.task_id;
      }
      updateMessage(currentChatId, assistantMsgId, (msg) => {
        const newMsg = { ...msg };
        
        switch (event.type) {
          case 'metadata':
            newMsg.model = event.data.model as ChatMessage["model"];
            break;
          case 'token':
            newMsg.content += String(event.data.content ?? event.data.token ?? "");
            break;
          case 'step': {
            if (!newMsg.steps) newMsg.steps = [];
            const rawType = event.data.type || "plan";
            const stepType = (rawType === "action" ? "act" : rawType === "observation" ? "observe" : rawType === "reflection" ? "reflect" : rawType) as AgentStep["type"];
            const stepId = `${String(event.data.step_number ?? event.data.step ?? 0)}:${stepType}`;
            const existingStepIdx = newMsg.steps.findIndex(s => s.id === stepId);
            if (existingStepIdx >= 0) {
              newMsg.steps[existingStepIdx].content = String(event.data.content ?? "");
            } else {
              newMsg.steps.push({
                id: stepId,
                type: stepType,
                content: String(event.data.content ?? ""),
                isComplete: false
              });
            }
            break;
          }
          case 'tool_result': {
            const stepId = `${String(event.data.step_number ?? event.data.step ?? 0)}:act`;
            if (newMsg.steps) {
              const sIdx = newMsg.steps.findIndex(s => s.id === stepId);
              if (sIdx >= 0) newMsg.steps[sIdx].isComplete = true;
            }
            if (typeof event.data.file_id === "string") {
              if (!newMsg.deliverables) newMsg.deliverables = [];
              const outputText = String(event.data.tool_output || '').toLowerCase();
              let fileType = 'docx';
              if (outputText.includes('.pdf')) fileType = 'pdf';
              else if (outputText.includes('.xlsx')) fileType = 'xlsx';
              else if (outputText.includes('.pptx')) fileType = 'pptx';
              
              const filename = typeof event.data.filename === "string"
                ? outputFilename(event.data.filename)
                : `Generated file ${event.data.file_id}`;
              newMsg.deliverables.push({
                id: event.data.file_id,
                filename,
                type: fileType,
                sizeBytes: typeof event.data.size_bytes === "number" ? event.data.size_bytes : undefined,
              });
            }
            break;
          }
          case 'done': {
            const status = event.data.status;
            if (status === "completed" || status === "failed" || status === "cancelled" || status === "stopped") {
              newMsg.status = status;
            }
            newMsg.truncated = event.data.truncated === true;
            newMsg.error = typeof event.data.error === "string" ? event.data.error : null;
            if (status === "failed" && newMsg.steps) {
              const failedIndex = newMsg.steps.map((step) => step.isComplete).lastIndexOf(false);
              if (failedIndex >= 0) newMsg.steps[failedIndex].isFailed = true;
            }
            newMsg.steps?.forEach((step) => { step.isComplete = true; });
            if (typeof event.data.task_id === "string") newMsg.taskId = event.data.task_id;
            if (Array.isArray(event.data.output_files)) {
              const existing = new Set((newMsg.deliverables || []).map((file) => file.id));
              for (const fileId of event.data.output_files) {
                if (typeof fileId === "string" && !existing.has(fileId)) {
                  newMsg.deliverables = [...(newMsg.deliverables || []), {
                    id: fileId,
                    filename: `Generated file ${fileId}`,
                    type: "docx",
                  }];
                }
              }
            }
            break;
          }
          case 'error': {
            const errDetail = String(event.data.error || event.data.detail || "Could not connect to the backend server.");
            newMsg.content += `\n\n**[Backend Notice]**: ${errDetail}`;
            break;
          }
        }
        return newMsg;
      });
    }, controller.signal);

    setIsStreaming(false);
    setStreamStartedAt(null);
    setStreamingMessageId(null);
    streamControllerRef.current = null;
    return true;
  };

  const handleCancel = async () => {
    streamControllerRef.current?.abort();
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      if (streamTaskIdRef.current) {
        await fetch(`${apiBase}/api/agent/tasks/${streamTaskIdRef.current}/cancel`, { method: "POST" });
      } else if (activeChatId) {
        await fetch(`${apiBase}/api/chat/stop`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ conversation_id: activeChatId }),
        });
      }
    } catch {
      toast.error("Unable to signal cancellation", { description: "The stream was stopped locally." });
    } finally {
      streamTaskIdRef.current = null;
      setIsStreaming(false);
      setStreamStartedAt(null);
      setStreamingMessageId(null);
    }
  };

  const hasUserMessage = messages.some((m: ChatMessage) => m.role === "user");



  return (
    <div className="h-[calc(100dvh-4rem)] min-h-0 flex flex-col overflow-hidden bg-background text-foreground">
      <ChatWorkflowModal 
        open={isWorkflowModalOpen} 
        onOpenChange={setIsWorkflowModalOpen} 
        messages={messages} 
      />

      <ChatArtifactsModal
        open={isArtifactsModalOpen}
        onOpenChange={setIsArtifactsModalOpen}
        artifacts={allArtifacts}
      />
      
      <div className="shrink-0 flex flex-wrap justify-end gap-2 border-b border-border p-3 sm:px-6">
        {hasArtifacts && (
          <button
            onClick={() => setIsArtifactsModalOpen(true)}
            className="flex min-h-8 items-center gap-2 rounded-[3px] border border-border bg-background px-3 font-mono text-xs font-medium text-foreground transition-colors hover:bg-muted active:translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <FileCode2 className="size-3.5 text-muted-foreground" />
            Artifacts <span className="text-muted-foreground">[{allArtifacts.length}]</span>
          </button>
        )}

        {hasUserMessage && (
          <button
            onClick={() => setIsWorkflowModalOpen(true)}
            className="flex min-h-8 items-center gap-2 rounded-[3px] border border-border bg-background px-3 font-mono text-xs font-medium text-foreground transition-colors hover:bg-muted active:translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <GitBranch className="size-3.5 text-muted-foreground" />
            Workflow trace
          </button>
        )}
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6">
        <div className={`mx-auto max-w-4xl ${!hasUserMessage ? 'min-h-full flex flex-col' : ''}`}>
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center">
              <p className="mb-4 text-sm font-mono text-muted-foreground">[+] LOCAL AGENT WORKBENCH</p>
              
              <h2 className="text-2xl font-bold mb-3 text-foreground">What do you need to inspect?</h2>
              <p className="text-gray-500 text-sm max-w-md mb-6 leading-relaxed">
                Ask a question, attach a document, or describe a deliverable. Kavach routes the task locally and streams each result.
              </p>
              
              
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div key={msg.id} className="mb-6">
                  {msg.role === "assistant" && msg.steps && msg.steps.length > 0 ? (
                    <div className="w-full py-3">
                      <AgentActivity steps={msg.steps} status={msg.id === streamingMessageId ? "working" : msg.status === "failed" ? "failed" : "complete"} />
                      {msg.id !== streamingMessageId && msg.content && <MessageBubble role={msg.role} content={msg.content} model={msg.model} />}
                    </div>
                  ) : msg.content === "" && msg.role === "assistant" && isStreaming ? (
                    <div className="flex w-full justify-center py-10">
                      <LoadingState variant="orbit" label="Generating response" startTime={streamStartedAt ?? undefined} />
                    </div>
                  ) : (
                  <MessageBubble 
                      role={msg.role}
                      content={msg.content}
                      model={msg.model}
                    />
                  )}
                  {msg.status && msg.status !== "completed" && (
                    <p className="ml-12 mb-3 text-xs text-destructive" role="status">
                      {msg.error || `Task ${msg.status}.`}
                    </p>
                  )}
                  {msg.truncated && (
                    <p className="ml-12 mb-3 text-xs text-amber-500" role="status">
                      Response truncated at the backend limit.
                    </p>
                  )}
                  
                  {/* Render Deliverables */}
                  {msg.deliverables && msg.deliverables.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {msg.deliverables.map(file => (
                        <DeliverableCard 
                          key={file.id} 
                          id={file.id} 
                          filename={file.filename} 
                          type={file.type as "docx" | "xlsx"} 
                          sizeBytes={file.sizeBytes}
                        />
                      ))}
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>
      
      {/* Suggestion Chips and Chat Window */}
      <div className="z-10 shrink-0 border-t border-border/50 bg-background p-3 sm:p-4">
        <ChatWindow 
          onSendMessage={handleSendMessage} 
          onCancel={handleCancel}
          isStreaming={isStreaming} 
        />
      </div>
    </div>
  );
}

