export function Topbar() {
  return (
    <div className="h-16 bg-background border-b border-border flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-4">
        <h1 className="text-foreground font-medium">MRPL Agentic Workbench</h1>
        <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20">
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          <span className="text-xs font-medium text-primary">Models Preloaded (~4.1 GB)</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-xs text-muted-foreground">
          Local Process: <span className="font-mono text-foreground">:8000</span>
        </div>
        <div className="w-8 h-8 rounded-full bg-sidebar-accent border border-border flex items-center justify-center text-sm font-bold text-sidebar-foreground">
          OP
        </div>
      </div>
    </div>
  );
}
