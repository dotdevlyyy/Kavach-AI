import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { v4 as uuidv4 } from 'uuid';
import { AgentStep } from '@/components/agent/AgentStepCard';

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  model?: "llama3.2:1b" | "qwen2.5-coder:1.5b" | "qwen2.5vl:3b";
  steps?: AgentStep[];
  deliverables?: any[];
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
    (set, get) => ({
      chats: [],
      activeChatId: null,
      isSidebarCollapsed: false,

      toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),

      setActiveChat: (id) => set({ activeChatId: id }),

      createChat: () => {
        const newChat: ChatSession = {
          id: uuidv4(),
          title: 'New Conversation',
          updatedAt: Date.now(),
          messages: [{
            id: uuidv4(),
            role: "assistant",
            content: "Welcome to the Kavach AI Workbench. I am connected securely to the MRPL air-gapped network.\n\nYou can ask me to:\n- Analyze P&ID diagrams (using Qwen-VL)\n- Generate secure python scripts (using Qwen-Coder)\n- Summarize refinery SOPs (using Llama 3.2)\n\nHow can I assist you today?",
            model: "llama3.2:1b"
          }]
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
    }
  )
);
