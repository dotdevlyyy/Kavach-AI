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
    createChat();
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

  const isSidebarCollapsed = useChatStore((state) => state.isSidebarCollapsed);

  return (
    <>
      {/* Mobile Backdrop */}
      {!isSidebarCollapsed && (
        <div 
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 md:hidden"
          onClick={() => useChatStore.getState().toggleSidebar()}
        />
      )}
      
      <div 
        className={`bg-sidebar border-r border-sidebar-border h-[100dvh] flex flex-col shrink-0 transition-all duration-300 ease-in-out overflow-hidden z-50 absolute md:relative ${
          isSidebarCollapsed ? "-translate-x-full w-64 md:w-16 md:translate-x-0" : "translate-x-0 w-64"
        }`}
      >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-center px-4 border-b border-sidebar-border shrink-0 whitespace-nowrap">
        <ShieldAlert className={`text-primary shrink-0 transition-all duration-300 ${isSidebarCollapsed ? "w-6 h-6" : "w-6 h-6 mr-3"}`} />
        <span className={`text-sidebar-foreground font-bold text-lg tracking-wider transition-all duration-300 ${isSidebarCollapsed ? "opacity-0 w-0 hidden" : "opacity-100"}`}>
          KAVACH AI
        </span>
      </div>

      <div className="flex-1 flex flex-col overflow-y-auto overflow-x-hidden [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        {/* Navigation Links */}
        <div className={`py-6 space-y-1 transition-all duration-300 ${isSidebarCollapsed ? "px-2" : "px-3"}`}>
          <div className={`text-xs font-semibold text-sidebar-foreground/50 uppercase tracking-wider mb-3 px-2 whitespace-nowrap transition-all duration-300 ${isSidebarCollapsed ? "opacity-0 hidden" : "opacity-100"}`}>
            System Menu
          </div>
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center py-2.5 rounded-md transition-all duration-300 text-sm overflow-hidden whitespace-nowrap ${
                  isSidebarCollapsed ? "justify-center px-0 gap-0" : "px-3 gap-3"
                } ${
                  isActive
                    ? "bg-sidebar-primary/10 text-sidebar-primary font-medium"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                }`}
                title={isSidebarCollapsed ? item.name : undefined}
              >
                <Icon className={`w-5 h-5 shrink-0 ${isActive ? "text-sidebar-primary" : ""}`} />
                <span className={`transition-all duration-300 ${isSidebarCollapsed ? "opacity-0 w-0 hidden" : "opacity-100"}`}>
                  {item.name}
                </span>
              </Link>
            );
          })}
        </div>

        {/* Chat History */}
        <div className={`px-3 pb-6 flex-1 transition-all duration-300 ${isSidebarCollapsed ? "opacity-0 invisible h-0 hidden" : "opacity-100"}`}>
          <div className="flex items-center justify-between text-xs font-semibold text-sidebar-foreground/50 uppercase tracking-wider mb-3 px-2 whitespace-nowrap">
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
              <div key={chat.id} className={`group flex items-center justify-between rounded transition-colors whitespace-nowrap overflow-hidden ${
                  activeChatId === chat.id && pathname === '/chat'
                    ? "bg-sidebar-accent text-sidebar-foreground" 
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                }`}
              >
                <button type="button" onClick={() => handleSelectChat(chat.id)} className="flex items-center gap-2 min-w-0 flex-1 px-3 py-2 text-left focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-primary">
                  <MessageCircle className={`w-4 h-4 shrink-0 ${activeChatId === chat.id && pathname === '/chat' ? "text-primary" : ""}`} />
                  <span className="text-sm truncate">{chat.title}</span>
                </button>
                <button 
                  onClick={(e) => handleDeleteChat(e, chat.id)}
                  aria-label={`Delete chat ${chat.title}`}
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity shrink-0 p-2 rounded focus-visible:opacity-100 focus-visible:outline-2 focus-visible:outline-primary"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
            {chats.length === 0 && (
              <div className="text-xs text-muted-foreground px-2 italic whitespace-nowrap">
                No recent chats
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Connection Status Footer */}
      <div className={`border-t border-sidebar-border shrink-0 transition-all duration-300 ${isSidebarCollapsed ? "p-2" : "p-4"}`}>
        <div className={`flex items-center rounded-md bg-secondary/10 border border-secondary/20 transition-all duration-300 whitespace-nowrap overflow-hidden ${isSidebarCollapsed ? "p-2 justify-center gap-0" : "px-2 py-2 gap-2"}`} title={isSidebarCollapsed ? "System Air-Gapped" : undefined}>
          <CheckCircle2 className="w-4 h-4 text-secondary shrink-0" />
          <span className={`text-xs font-medium text-secondary-foreground truncate transition-all duration-300 ${isSidebarCollapsed ? "opacity-0 w-0 hidden" : "opacity-100"}`}>
            System Air-Gapped
          </span>
        </div>
      </div>
    </div>
    </>
  );
}
