import { Dialog, DialogContent, DialogTitle, DialogClose } from "@/components/ui/dialog";
import { ReactFlow, Background, Controls, Handle, Position } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { XIcon } from "lucide-react";
import { useTheme } from "next-themes";

interface WorkflowData {
  label: string;
  description: string;
  content: string;
  footer: string;
  accent: string;
  accentText?: string;
  glow?: string;
  target: boolean;
  source: boolean;
}

const nodeIds = {
  start: "start",
  classify: "classify",
  routeGeneral: "route-general",
  routeRefund: "route-refund",
  routeTechnical: "route-technical",
  complete: "complete",
};

const initialNodes = [
  {
    id: nodeIds.start,
    type: "workflow",
    position: { x: 50, y: 300 },
    data: {
      label: "Start Workflow",
      description: "Initialize routing workflow",
      content: "Input: Customer Query",
      footer: "Setup: globalThis.fetch = fetch",
      accent: "bg-sidebar-accent/50",
      target: false,
      source: true,
    }
  },
  {
    id: nodeIds.classify,
    type: "workflow",
    position: { x: 450, y: 300 },
    data: {
      label: "Classify Query",
      description: "Determine type and complexity",
      content: "Classify: type (general, refund, technical) + complexity (simple, complex)",
      footer: "Model: deepseek/deepseek-v4-flash-0731 • Step 1",
      accent: "bg-primary/10",
      accentText: "text-primary",
      glow: "shadow-[0_0_15px_rgba(245,158,11,0.15)] border-primary/50",
      target: true,
      source: true,
    }
  },
  {
    id: nodeIds.routeGeneral,
    type: "workflow",
    position: { x: 900, y: 50 },
    data: {
      label: "Route: General",
      description: "Handle general inquiries",
      content: "Expert customer service agent • Model: gpt-4o-mini (simple) / o4-mini (complex)",
      footer: "Conditional routing",
      accent: "bg-sidebar-accent/50",
      target: true,
      source: true,
    }
  },
  {
    id: nodeIds.routeRefund,
    type: "workflow",
    position: { x: 900, y: 300 },
    data: {
      label: "Route: Refund",
      description: "Handle refund requests",
      content: "Refund specialist • Follow policy • Model: gpt-4o-mini (simple) / o4-mini (complex)",
      footer: "Conditional routing",
      accent: "bg-sidebar-accent/50",
      target: true,
      source: true,
    }
  },
  {
    id: nodeIds.routeTechnical,
    type: "workflow",
    position: { x: 900, y: 550 },
    data: {
      label: "Route: Technical",
      description: "Handle technical support",
      content: "Technical specialist • Step-by-step troubleshooting • Model: gpt-4o-mini (simple) / o4-mini (complex)",
      footer: "Conditional routing",
      accent: "bg-sidebar-accent/50",
      target: true,
      source: true,
    }
  },
  {
    id: nodeIds.complete,
    type: "workflow",
    position: { x: 1350, y: 300 },
    data: {
      label: "Complete",
      description: "Workflow finished",
      content: "Response generated based on classification",
      footer: "Status: Success",
      accent: "bg-emerald-500/10",
      accentText: "text-emerald-500",
      glow: "shadow-[0_0_15px_rgba(16,185,129,0.15)] border-emerald-500/50",
      target: true,
      source: false,
    }
  }
];

const initialEdges = [
  { id: "e1", source: nodeIds.start, target: nodeIds.classify, animated: true },
  { id: "e2", source: nodeIds.classify, target: nodeIds.routeGeneral, animated: true },
  { id: "e3", source: nodeIds.classify, target: nodeIds.routeRefund, animated: true },
  { id: "e4", source: nodeIds.classify, target: nodeIds.routeTechnical, animated: true },
  { id: "e5", source: nodeIds.routeGeneral, target: nodeIds.complete, animated: true },
  { id: "e6", source: nodeIds.routeRefund, target: nodeIds.complete, animated: true },
  { id: "e7", source: nodeIds.routeTechnical, target: nodeIds.complete, animated: true },
];

function WorkflowNode({ data }: { data: WorkflowData }) {
  return (
    <div className={`w-[280px] bg-card border border-border rounded-xl shadow-lg flex flex-col overflow-hidden relative z-10 transition-colors ${data.glow || "hover:border-primary/50"}`}>
      {data.target && (
        <Handle type="target" position={Position.Left} className="w-3 h-3 bg-foreground border-2 border-background" />
      )}
      
      <div className={`p-3 border-b border-border ${data.accent}`}>
        <h3 className={`font-bold text-sm ${data.accentText || "text-foreground"}`}>{data.label}</h3>
        <p className={`text-[10px] ${data.accentText ? "opacity-80" : "text-muted-foreground"}`}>{data.description}</p>
      </div>
      <div className="p-4 text-xs text-foreground bg-card min-h-[70px]">
        {data.content}
      </div>
      <div className={`p-2 bg-sidebar-accent/30 text-[10px] ${data.accentText || "text-muted-foreground"} font-mono border-t border-border flex items-center gap-1`}>
        {data.accentText && data.label === "Complete" && <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />}
        {data.footer}
      </div>

      {data.source && (
        <Handle type="source" position={Position.Right} className="w-3 h-3 bg-foreground border-2 border-background" />
      )}
    </div>
  );
}

const nodeTypes = { workflow: WorkflowNode };

interface RoutingWorkflowModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RoutingWorkflowModal({ open, onOpenChange }: RoutingWorkflowModalProps) {
  const { theme } = useTheme();
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="!max-w-[100vw] sm:!max-w-[100vw] !w-screen !h-screen !rounded-none flex flex-col bg-background border-none p-0 overflow-hidden">
        <div className="p-6 border-b border-border bg-card shadow-sm z-20 relative flex items-center justify-between">
          <div>
            <DialogTitle className="text-xl font-bold text-foreground">Routing Workflow Pattern</DialogTitle>
            <p className="text-sm text-muted-foreground mt-1">Autonomous request classification and conditional routing using AI SDK</p>
          </div>
          <DialogClose className="p-2 rounded-lg hover:bg-sidebar-accent text-muted-foreground transition-colors">
            <XIcon className="w-5 h-5" />
            <span className="sr-only">Close</span>
          </DialogClose>
        </div>
        
        <div className="flex-1 w-full h-full relative">
          <ReactFlow
            nodes={initialNodes}
            edges={initialEdges}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            className="bg-background"
            colorMode={theme === "dark" ? "dark" : "light"}
          >
            <Background gap={16} size={1} />
            <Controls />
          </ReactFlow>
        </div>
      </DialogContent>
    </Dialog>
  );
}
