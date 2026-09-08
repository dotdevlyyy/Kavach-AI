"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { User, Settings, LogOut, ShieldAlert } from "lucide-react";
import { toast } from "sonner";

import { AnimatedThemeToggler } from "./AnimatedThemeToggler";

export function Topbar() {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    setIsDropdownOpen(false);
    toast.success("Secure Logout Initiated", {
      description: "Clearing session data and locking terminal...",
    });
    // Real logout logic goes here
  };

  return (
    <div className="h-16 bg-background border-b border-border flex items-center justify-between px-6 shrink-0 relative z-50">
      <div className="flex items-center gap-4">
        <h1 className="text-foreground font-medium">MRPL Agentic Workbench</h1>
        <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20">
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          <span className="text-xs font-medium text-primary">Models Preloaded (~4.1 GB)</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-xs text-muted-foreground hidden sm:block">
          Local Process: <span className="font-mono text-foreground">:8000</span>
        </div>
        
        <AnimatedThemeToggler />

        {/* Clickable Profile Avatar */}
        <div className="relative" ref={dropdownRef}>
          <button 
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className={`w-9 h-9 rounded-full border flex items-center justify-center text-sm font-bold transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background ${
              isDropdownOpen 
                ? "bg-primary text-primary-foreground border-primary" 
                : "bg-sidebar-accent border-border text-sidebar-foreground hover:bg-sidebar-accent/80 hover:border-primary/50"
            }`}
          >
            OP
          </button>

          {/* Dropdown Menu */}
          {isDropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-card border border-border rounded-xl shadow-lg overflow-hidden flex flex-col animate-in fade-in slide-in-from-top-2">
              <div className="px-4 py-3 border-b border-border bg-sidebar/50">
                <p className="text-sm font-medium text-foreground">Plant Operator</p>
                <p className="text-xs text-muted-foreground font-mono mt-0.5">ID: OP-7492-MRPL</p>
                <div className="flex items-center gap-1 mt-2 text-[10px] font-bold text-emerald-500 uppercase tracking-wider">
                  <ShieldAlert className="w-3 h-3" />
                  Clearance Level 4
                </div>
              </div>
              
              <div className="p-1 flex flex-col">
                <button className="flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-sidebar-accent rounded-md transition-colors w-full text-left">
                  <User className="w-4 h-4 text-muted-foreground" />
                  Operator Profile
                </button>
                <button 
                  onClick={() => {
                    setIsDropdownOpen(false);
                    router.push('/settings');
                  }}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-sidebar-accent rounded-md transition-colors w-full text-left"
                >
                  <Settings className="w-4 h-4 text-muted-foreground" />
                  System Settings
                </button>
              </div>
              
              <div className="p-1 border-t border-border">
                <button 
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-destructive hover:bg-destructive/10 rounded-md transition-colors w-full text-left font-medium"
                >
                  <LogOut className="w-4 h-4" />
                  Secure Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
