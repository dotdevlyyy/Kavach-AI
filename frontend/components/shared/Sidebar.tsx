"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { 
  ShieldAlert, 
  MessageSquare, 
  Database, 
  Activity, 
  Settings, 
  CheckCircle2,
  FolderOpen,
  PlusCircle,
  MessageCircle,
  Trash2
} from "lucide-react";
import { useChatStore } from "@/lib/store";

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  
  const chats = useChatStore((state) => state.chats);
  const activeChatId = useChatStore((state) => state.activeChatId);
  const createChat = useChatStore((state) => state.createChat);
  const deleteChat = useChatStore((state) => state.deleteChat);
  const setActiveChat = useChatStore((state) => state.setActiveChat);

  const navItems = [
    { name: "Dashboard", href: "/", icon: Activity },
    { name: "Agent Chat", href: "/chat", icon: MessageSquare },
    { name: "Task History", href: "/tasks", icon: FolderOpen },
    { name: "KB Manager", href: "/knowledge", icon: Database },
    { name: "Network Audit", href: "/network", icon: ShieldAlert },
    { name: "Settings", href: "/settings", icon: Settings },
  ];

  const handleNewChat = () => {
    const newId = createChat();
    router.push('/chat');
  };

  const handleSelectChat = (id: string) => {
    setActiveChat(id);
    router.push('/chat');
  };

  const handleDeleteChat = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    deleteChat(id);
  };

  return (
    <div className="w-64 bg-sidebar border-r border-sidebar-border h-screen flex flex-col shrink-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-sidebar-border shrink-0">
        <ShieldAlert className="text-primary w-6 h-6 mr-3" />
        <span className="text-sidebar-foreground font-bold text-lg tracking-wider">KAVACH AI</span>
      </div>

      <div className="flex-1 flex flex-col overflow-y-auto">
        {/* Navigation Links */}
        <div className="py-6 px-4 space-y-1">
          <div className="text-xs font-semibold text-sidebar-foreground/50 uppercase tracking-wider mb-3 px-2">
            System Menu
          </div>
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors ${
                  isActive
                    ? "bg-sidebar-primary/10 text-sidebar-primary font-medium"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? "text-sidebar-primary" : ""}`} />
                {item.name}
              </Link>
            );
          })}
        </div>

        {/* Chat History */}
        <div className="px-4 pb-6 flex-1">
          <div className="flex items-center justify-between text-xs font-semibold text-sidebar-foreground/50 uppercase tracking-wider mb-3 px-2">
            <span>Recent Chats</span>
            <button 
              onClick={handleNewChat}
              className="hover:text-primary transition-colors cursor-pointer p-1" 
              title="New Chat"
            >
              <PlusCircle className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-1">
            {chats.map((chat) => (
              <div 
                key={chat.id} 
                onClick={() => handleSelectChat(chat.id)}
                className={`group flex items-center justify-between px-3 py-2 rounded-md transition-colors cursor-pointer ${
                  activeChatId === chat.id && pathname === '/chat'
                    ? "bg-sidebar-accent text-sidebar-foreground" 
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                }`}
              >
                <div className="flex items-center gap-2 overflow-hidden">
                  <MessageCircle className={`w-4 h-4 shrink-0 ${activeChatId === chat.id && pathname === '/chat' ? "text-primary" : ""}`} />
                  <span className="text-sm truncate">{chat.title}</span>
                </div>
                <button 
                  onClick={(e) => handleDeleteChat(e, chat.id)}
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all shrink-0 p-1"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
            {chats.length === 0 && (
              <div className="text-xs text-muted-foreground px-2 italic">
                No recent chats
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Connection Status Footer */}
      <div className="p-4 border-t border-sidebar-border shrink-0">
        <div className="flex items-center gap-2 px-2 py-2 rounded-md bg-secondary/10 border border-secondary/20">
          <CheckCircle2 className="w-4 h-4 text-secondary shrink-0" />
          <span className="text-xs font-medium text-secondary-foreground truncate">
            System Air-Gapped
          </span>
        </div>
      </div>
    </div>
  );
}
