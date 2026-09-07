"use client";

import { useState, useRef, useEffect } from "react";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { AgentStepCard } from "@/components/agent/AgentStepCard";
import { DeliverableCard } from "@/components/agent/DeliverableCard";
import { consumeSSEStream, uploadFiles, StreamEvent } from "@/lib/StreamConsumer";
import { useChatStore, ChatMessage } from "@/lib/store";
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

    const isAgentTask = message.toLowerCase().includes("plan") || message.toLowerCase().includes("execute");
    const endpoint = isAgentTask ? "http://localhost:8000/api/agent/execute" : "http://localhost:8000/api/chat";
    const payload = isAgentTask 
      ? { task_description: message, files: fileIds, max_steps: 10 } 
      : { message: message, files: fileIds };

    await consumeSSEStream(endpoint, payload, (event: StreamEvent) => {
      updateMessage(currentChatId, assistantMsgId, (msg) => {
        const newMsg = { ...msg };
        
        switch (event.type) {
          case 'metadata':
            newMsg.model = event.data.model;
            break;
          case 'token':
            newMsg.content += event.data.content;
            break;
          case 'step':
            if (!newMsg.steps) newMsg.steps = [];
            const existingStepIdx = newMsg.steps.findIndex(s => s.id === event.data.step_number.toString());
            if (existingStepIdx >= 0) {
              newMsg.steps[existingStepIdx].content += event.data.content;
            } else {
              newMsg.steps.push({
                id: event.data.step_number.toString(),
                type: event.data.type,
                content: event.data.content,
                isComplete: false
              });
            }
            break;
          case 'tool_result':
            if (newMsg.steps) {
              const sIdx = newMsg.steps.findIndex(s => s.id === event.data.step_number.toString());
              if (sIdx >= 0) newMsg.steps[sIdx].isComplete = true;
            }
            if (event.data.file_id) {
              if (!newMsg.deliverables) newMsg.deliverables = [];
              newMsg.deliverables.push({
                id: event.data.file_id,
                filename: event.data.tool_output,
                type: event.data.tool_output.endsWith('.docx') ? 'docx' : 'xlsx'
              });
            }
            break;
        }
        return newMsg;
      });
    });

    setIsStreaming(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
        <div className="max-w-4xl mx-auto">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground mt-20">
              <h2 className="text-xl font-bold mb-2">Kavach AI Workbench Ready</h2>
              <p>System is air-gapped. Connects locally to Ollama on port 11434.</p>
            </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className="mb-6">
              <MessageBubble 
                role={msg.role}
                content={msg.content}
                model={msg.model}
              />
              
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
        </div>
      </div>
      <div className="p-4 bg-background border-t border-border shrink-0">
        <ChatWindow 
          onSendMessage={handleSendMessage} 
          isStreaming={isStreaming} 
        />
      </div>
    </div>
  );
}

