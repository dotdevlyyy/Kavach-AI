"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export function AnimatedThemeToggler() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return <div className="w-9 h-9" />; // Placeholder to prevent hydration mismatch

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="relative flex items-center justify-center w-9 h-9 rounded-full bg-sidebar-accent border border-border text-sidebar-foreground hover:bg-sidebar-accent/80 transition-colors focus:outline-none overflow-hidden"
      aria-label="Toggle theme"
    >
      <Sun className="h-4 w-4 transition-all duration-500 rotate-0 scale-100 dark:-rotate-90 dark:scale-0 absolute" />
      <Moon className="h-4 w-4 transition-all duration-500 rotate-90 scale-0 dark:rotate-0 dark:scale-100 absolute" />
    </button>
  );
}
