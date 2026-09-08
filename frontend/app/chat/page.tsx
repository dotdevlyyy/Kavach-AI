"use client";

import { useState, useRef, useEffect } from "react";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { AgentStepCard } from "@/components/agent/AgentStepCard";
import { DeliverableCard } from "@/components/agent/DeliverableCard";
import { consumeSSEStream, uploadFiles, StreamEvent } from "@/lib/StreamConsumer";
import { useChatStore } from "@/lib/store";
import { v4 as uuidv4 } from 'uuid';

export default function ChatPage() {
  const activeChatId = useChatStore((state) => state.activeChatId);
  const chats = useChatStore((state) => state.chats);
  const addMessage = useChatStore((state) => state.addMessage);
  const updateMessage = useChatStore((state) => state.updateMessage);
  const createChat = useChatStore((state) => state.createChat);

  // Initialize a chat if none exists
  useEffect(() => {
    if (chats.length === 0) {
      createChat();
    }
  }, [chats.length, createChat]);

  const activeChat = chats.find(c => c.id === activeChatId) || chats[0];
  const messages = activeChat?.messages || [];

  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (message: string, files: File[]) => {
    if (!activeChatId) return;
    const currentChatId = activeChatId;

    let fileIds: string[] = [];
    if (files.length > 0) {
      fileIds = await uploadFiles(files);
    }

    const userMsgId = uuidv4();
    addMessage(currentChatId, {
      id: userMsgId,
      role: "user",
      content: message + (files.length > 0 ? `\n\n*[Attached ${files.length} files]*` : "")
    });
    
    setIsStreaming(true);
    
    const assistantMsgId = uuidv4();
    addMessage(currentChatId, {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      steps: [],
      deliverables: []
    });

    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const isAgentTask = message.toLowerCase().includes("plan") || message.toLowerCase().includes("execute");
    const endpoint = isAgentTask ? `${apiBase}/api/agent/execute` : `${apiBase}/api/chat`;
    const payload = isAgentTask 
      ? { task_description: message, file_ids: fileIds, files: fileIds, max_steps: 10 } 
      : { message: message, file_ids: fileIds, files: fileIds };

    await consumeSSEStream(endpoint, payload, (event: StreamEvent) => {
      updateMessage(currentChatId, assistantMsgId, (msg) => {
        const newMsg = { ...msg };
        
        switch (event.type) {
          case 'metadata':
            newMsg.model = event.data.model;
            break;
          case 'token':
            newMsg.content += (event.data.content ?? event.data.token ?? "");
            break;
          case 'step': {
            if (!newMsg.steps) newMsg.steps = [];
            const stepId = (event.data.step_number ?? event.data.step ?? 0).toString();
            const rawType = event.data.type || "plan";
            const stepType = (rawType === "action" ? "act" : rawType === "observation" ? "observe" : rawType === "reflection" ? "reflect" : rawType) as any;
            const existingStepIdx = newMsg.steps.findIndex(s => s.id === stepId);
            if (existingStepIdx >= 0) {
              newMsg.steps[existingStepIdx].content += event.data.content;
            } else {
              newMsg.steps.push({
                id: stepId,
                type: stepType,
                content: event.data.content,
                isComplete: false
              });
            }
            break;
          }
          case 'tool_result': {
            const stepId = (event.data.step_number ?? event.data.step ?? 0).toString();
            if (newMsg.steps) {
              const sIdx = newMsg.steps.findIndex(s => s.id === stepId);
              if (sIdx >= 0) newMsg.steps[sIdx].isComplete = true;
            }
            if (event.data.file_id) {
              if (!newMsg.deliverables) newMsg.deliverables = [];
              newMsg.deliverables.push({
                id: event.data.file_id,
                filename: event.data.tool_output || event.data.file_id,
                type: (event.data.tool_output || '').endsWith('.xlsx') ? 'xlsx' : 'docx'
              });
            }
            break;
          }
          case 'error': {
            const errDetail = event.data.error || event.data.detail || "Could not connect to the backend server.";
            newMsg.content += `\n\n**[Backend Notice]**: ${errDetail}`;
            break;
          }
        }
        return newMsg;
      });
    });

    setIsStreaming(false);
  };

  const hasUserMessage = messages.some((m: any) => m.role === "user");

  return (
    <div className="min-h-full flex flex-col bg-white text-black">
      <div className="flex-1 p-6">
        <div className={`max-w-4xl mx-auto ${!hasUserMessage ? 'min-h-[calc(100vh-200px)] flex flex-col' : ''}`}>
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center mt-[-100px]">
              <div className="flex items-center justify-center gap-4 mb-4 text-gray-700">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              </div>
              
              <h2 className="text-2xl font-bold mb-3 text-black">Sub-Agent Orchestrator</h2>
              <p className="text-gray-500 text-sm max-w-md mb-6 leading-relaxed">
                A custom Agent implementation that routes requests to specialized sub-agents. The orchestrator analyzes your query and delegates to the appropriate agent: <span className="bg-gray-100 border border-gray-200 rounded px-1.5 py-0.5 text-xs text-gray-700 font-mono">research</span>, <span className="bg-gray-100 border border-gray-200 rounded px-1.5 py-0.5 text-xs text-gray-700 font-mono">analysis</span>, or <span className="bg-gray-100 border border-gray-200 rounded px-1.5 py-0.5 text-xs text-gray-700 font-mono">support</span>.
              </p>
              
              <div className="flex items-center gap-3 text-gray-400 text-xs">
                <span className="flex items-center gap-1 border border-gray-200 bg-gray-50 rounded px-2 py-1"><span className="text-[10px]">✨</span> tool()</span>
                <span className="flex items-center gap-1 border border-gray-200 bg-gray-50 rounded px-2 py-1">ToolLoopAgent</span>
                <span className="flex items-center gap-1 border border-gray-200 bg-gray-50 rounded px-2 py-1">stepCountIs()</span>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div key={msg.id} className="mb-6">
                  {msg.content === "" && msg.role === "assistant" && isStreaming ? (
                    <div className="flex w-full justify-center py-10">
                      <div className="w-6 h-6 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
                    </div>
                  ) : (
                    <MessageBubble 
                      role={msg.role}
                      content={msg.content}
                      model={msg.model}
                    />
                  )}
                  
                  {/* Render Agent Steps inside the message area if any */}
                  {msg.steps && msg.steps.length > 0 && (
                    <div className="ml-12 mr-12 mb-4">
                      {msg.steps.map(step => (
                        <AgentStepCard key={step.id} step={step} />
                      ))}
                    </div>
                  )}

                  {/* Render Deliverables */}
                  {msg.deliverables && msg.deliverables.length > 0 && (
                    <div className="ml-12 mr-12 flex flex-wrap gap-2">
                      {msg.deliverables.map(file => (
                        <DeliverableCard 
                          key={file.id} 
                          id={file.id} 
                          filename={file.filename} 
                          type={file.type} 
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
      <div className="sticky bottom-0 z-10 p-4 bg-white shrink-0 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
        {messages.length === 0 && (
          <div className="max-w-4xl mx-auto flex gap-2 mb-3 px-2 overflow-x-auto">
            <button className="whitespace-nowrap px-3 py-1.5 bg-gray-50 border border-gray-200 text-gray-700 text-xs rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-1.5">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
              Research the latest trends in AI development
            </button>
            <button className="whitespace-nowrap px-3 py-1.5 bg-gray-50 border border-gray-200 text-gray-700 text-xs rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-1.5">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
              Analyze the pros and cons of microservices architecture
            </button>
            <button className="whitespace-nowrap px-3 py-1.5 bg-gray-50 border border-gray-200 text-gray-700 text-xs rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-1.5">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              How do I deploy...
            </button>
          </div>
        )}
        <ChatWindow 
          onSendMessage={handleSendMessage} 
          isStreaming={isStreaming} 
        />
      </div>
    </div>
  );
}

