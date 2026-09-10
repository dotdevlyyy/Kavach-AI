import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { v4 as uuidv4 } from 'uuid';
import { AgentStep } from '@/components/agent/AgentStepCard';

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  model?: "llama3.2:1b" | "qwen2.5-coder:1.5b" | "qwen2.5vl:3b";
  status?: "completed" | "failed" | "cancelled" | "stopped";
  truncated?: boolean;
  error?: string | null;
  taskId?: string;
  steps?: AgentStep[];
  deliverables?: { id: string; filename: string; type: string; sizeBytes?: number; url?: string; content?: string }[];
  attachedFiles?: { id: string; name: string; type: string; url?: string }[];
}

export interface ChatSession {
  id: string;
  title: string;
  updatedAt: number;
  messages: ChatMessage[];
}

interface ChatStore {
  chats: ChatSession[];
  activeChatId: string | null;
  hasHydrated: boolean;
  setHasHydrated: (hasHydrated: boolean) => void;
  setActiveChat: (id: string | null) => void;
  createChat: () => string;
  deleteChat: (id: string) => void;
  addMessage: (chatId: string, message: ChatMessage) => void;
  updateMessage: (chatId: string, messageId: string, updater: (msg: ChatMessage) => ChatMessage) => void;
  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      chats: [],
      activeChatId: null,
      hasHydrated: false,
      isSidebarCollapsed: false,

      setHasHydrated: (hasHydrated) => set({ hasHydrated }),

      toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),

      setActiveChat: (id) => set({ activeChatId: id }),

      createChat: () => {
        const newChat: ChatSession = {
          id: uuidv4(),
          title: 'New Conversation',
          updatedAt: Date.now(),
          messages: []
        };
        set((state) => ({
          chats: [newChat, ...state.chats],
          activeChatId: newChat.id
        }));
        return newChat.id;
      },

      deleteChat: (id) => set((state) => {
        const newChats = state.chats.filter(c => c.id !== id);
        return {
          chats: newChats,
          activeChatId: state.activeChatId === id ? (newChats[0]?.id || null) : state.activeChatId
        };
      }),

      addMessage: (chatId, message) => set((state) => {
        return {
          chats: state.chats.map(chat => {
            if (chat.id === chatId) {
              // Generate title from first user message if it's "New Conversation"
              let newTitle = chat.title;
              if (chat.title === 'New Conversation' && message.role === 'user') {
                newTitle = message.content.slice(0, 30) + (message.content.length > 30 ? '...' : '');
              }
              return {
                ...chat,
                title: newTitle,
                updatedAt: Date.now(),
                messages: [...chat.messages, message]
              };
            }
            return chat;
          }).sort((a, b) => b.updatedAt - a.updatedAt)
        };
      }),

      updateMessage: (chatId, messageId, updater) => set((state) => ({
        chats: state.chats.map(chat => {
          if (chat.id === chatId) {
            return {
              ...chat,
              messages: chat.messages.map(msg => 
                msg.id === messageId ? updater(msg) : msg
              )
            };
          }
          return chat;
        })
      })),
    }),
    {
      name: 'kavach-chat-storage',
      onRehydrateStorage: () => (state) => state?.setHasHydrated(true),
    }
  )
);
