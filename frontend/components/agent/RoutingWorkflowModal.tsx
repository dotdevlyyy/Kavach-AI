import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";

interface RoutingWorkflowModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RoutingWorkflowModal({ open, onOpenChange }: RoutingWorkflowModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] w-[1300px] h-[85vh] flex flex-col bg-background border-border p-0 overflow-hidden rounded-xl">
        <div className="p-5 border-b border-border bg-card shadow-sm z-20 relative">
          <DialogTitle className="text-xl font-bold text-foreground">Routing Workflow Pattern</DialogTitle>
          <p className="text-sm text-muted-foreground mt-1">Autonomous request classification and conditional routing</p>
        </div>
        
        <div className="flex-1 overflow-auto relative p-8 bg-[radial-gradient(#1e293b_1px,transparent_1px)] dark:bg-[radial-gradient(#222222_1px,transparent_1px)] [background-size:16px_16px] flex items-center justify-center">
          
          <div className="flex items-center gap-12 relative z-10 scale-[0.85] origin-center">
            
            {/* Step 1 */}
            <div className="flex-shrink-0 w-[260px] bg-card border border-border rounded-xl shadow-lg flex flex-col overflow-hidden relative">
              <div className="p-3 border-b border-border bg-sidebar-accent/50">
                <h3 className="font-bold text-sm text-foreground">Start Workflow</h3>
                <p className="text-[10px] text-muted-foreground">Initialize routing workflow</p>
              </div>
              <div className="p-4 text-xs text-foreground bg-card min-h-[70px]">
                Input: Customer Query
              </div>
              <div className="p-2 bg-sidebar-accent/30 text-[10px] text-muted-foreground font-mono border-t border-border">
                Setup: globalThis.fetch = fetch
              </div>
              {/* Connector right */}
              <div className="absolute top-1/2 -right-12 w-12 h-[2px] bg-border -translate-y-1/2">
                <div className="w-2 h-2 rounded-full bg-foreground absolute top-1/2 left-0 -translate-y-1/2" />
                <div className="w-2 h-2 rounded-full bg-foreground absolute top-1/2 right-0 -translate-y-1/2" />
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex-shrink-0 w-[260px] bg-card border border-primary/50 shadow-[0_0_15px_rgba(245,158,11,0.15)] rounded-xl flex flex-col overflow-hidden relative">
              <div className="p-3 border-b border-border bg-primary/10">
                <h3 className="font-bold text-sm text-primary">Classify Query</h3>
                <p className="text-[10px] text-primary/70">Determine type and complexity</p>
              </div>
              <div className="p-4 text-xs text-foreground bg-card min-h-[70px]">
                Classify: type (general, refund, technical) + complexity (simple, complex)
              </div>
              <div className="p-2 bg-sidebar-accent/30 text-[10px] text-muted-foreground font-mono border-t border-border">
                Model: deepseek/deepseek-v4-flash-0731
              </div>

              {/* Connector right branching */}
              <div className="absolute top-1/2 -right-12 w-12 h-[2px] bg-border -translate-y-1/2">
                <div className="w-2 h-2 rounded-full bg-primary absolute top-1/2 left-0 -translate-y-1/2" />
              </div>
            </div>

            {/* Step 3 (Branching) */}
            <div className="flex flex-col gap-8 flex-shrink-0 relative">
              {/* Vertical branch line */}
              <div className="absolute left-[-48px] top-[15%] bottom-[15%] w-[2px] bg-border rounded-full" />
              <div className="absolute left-[-48px] top-[15%] w-12 h-[2px] bg-border" />
              <div className="absolute left-[-48px] top-[50%] w-12 h-[2px] bg-border -translate-y-1/2" />
              <div className="absolute left-[-48px] bottom-[15%] w-12 h-[2px] bg-border" />
              
              {/* Right merging line */}
              <div className="absolute right-[-48px] top-[15%] bottom-[15%] w-[2px] bg-border rounded-full" />
              <div className="absolute right-[-48px] top-[15%] w-12 h-[2px] bg-border" />
              <div className="absolute right-[-48px] top-[50%] w-12 h-[2px] bg-border -translate-y-1/2" />
              <div className="absolute right-[-48px] bottom-[15%] w-12 h-[2px] bg-border" />
              
              {/* Dot indicators on branches left */}
              <div className="w-2 h-2 rounded-full bg-foreground absolute top-[15%] left-[-4px] -translate-y-1/2" />
              <div className="w-2 h-2 rounded-full bg-foreground absolute top-[50%] left-[-4px] -translate-y-1/2" />
              <div className="w-2 h-2 rounded-full bg-foreground absolute bottom-[15%] left-[-4px] translate-y-1/2" />

              {/* Dot indicators on branches right */}
              <div className="w-2 h-2 rounded-full bg-foreground absolute top-[15%] right-[-4px] -translate-y-1/2" />
              <div className="w-2 h-2 rounded-full bg-foreground absolute top-[50%] right-[-4px] -translate-y-1/2" />
              <div className="w-2 h-2 rounded-full bg-foreground absolute bottom-[15%] right-[-4px] translate-y-1/2" />


              <div className="w-[280px] bg-card border border-border rounded-xl shadow-lg flex flex-col overflow-hidden relative z-10 group hover:border-primary/50 transition-colors">
                <div className="p-3 border-b border-border bg-sidebar-accent/50">
                  <h3 className="font-bold text-sm text-foreground group-hover:text-primary transition-colors">Route: General</h3>
                  <p className="text-[10px] text-muted-foreground">Handle general inquiries</p>
                </div>
                <div className="p-4 text-xs text-foreground bg-card min-h-[70px]">
                  Expert customer service agent • Model: gpt-4o-mini (simple) / o4-mini (complex)
                </div>
                <div className="p-2 bg-sidebar-accent/30 text-[10px] text-muted-foreground font-mono border-t border-border">
                  Conditional routing
                </div>
              </div>
              
              <div className="w-[280px] bg-card border border-border rounded-xl shadow-lg flex flex-col overflow-hidden relative z-10 group hover:border-primary/50 transition-colors">
                <div className="p-3 border-b border-border bg-sidebar-accent/50">
                  <h3 className="font-bold text-sm text-foreground group-hover:text-primary transition-colors">Route: Refund</h3>
                  <p className="text-[10px] text-muted-foreground">Handle refund requests</p>
                </div>
                <div className="p-4 text-xs text-foreground bg-card min-h-[70px]">
                  Refund specialist • Follow policy • Model: gpt-4o-mini (simple) / o4-mini (complex)
                </div>
                <div className="p-2 bg-sidebar-accent/30 text-[10px] text-muted-foreground font-mono border-t border-border">
                  Conditional routing
                </div>
              </div>

              <div className="w-[280px] bg-card border border-border rounded-xl shadow-lg flex flex-col overflow-hidden relative z-10 group hover:border-primary/50 transition-colors">
                <div className="p-3 border-b border-border bg-sidebar-accent/50">
                  <h3 className="font-bold text-sm text-foreground group-hover:text-primary transition-colors">Route: Technical</h3>
                  <p className="text-[10px] text-muted-foreground">Handle technical support</p>
                </div>
                <div className="p-4 text-xs text-foreground bg-card min-h-[70px]">
                  Technical specialist • Step-by-step troubleshooting • Model: gpt-4o-mini (simple) / o4-mini (complex)
                </div>
                <div className="p-2 bg-sidebar-accent/30 text-[10px] text-muted-foreground font-mono border-t border-border">
                  Conditional routing
                </div>
              </div>
            </div>

            {/* Step 4 */}
            <div className="flex-shrink-0 w-[260px] bg-card border border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.15)] rounded-xl flex flex-col overflow-hidden relative">
              <div className="absolute top-1/2 -left-12 w-12 h-[2px] bg-border -translate-y-1/2">
                <div className="w-2 h-2 rounded-full bg-emerald-500 absolute top-1/2 right-0 -translate-y-1/2" />
              </div>
              
              <div className="p-3 border-b border-border bg-emerald-500/10">
                <h3 className="font-bold text-sm text-emerald-500">Complete</h3>
                <p className="text-[10px] text-emerald-500/70">Workflow finished</p>
              </div>
              <div className="p-4 text-xs text-foreground bg-card min-h-[70px]">
                Response generated based on classification
              </div>
              <div className="p-2 bg-sidebar-accent/30 text-[10px] text-muted-foreground font-mono border-t border-border flex items-center gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Status: Success
              </div>
            </div>

          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
