import { Dialog, DialogContent, DialogTitle, DialogClose } from "@/components/ui/dialog";
import { ReactFlow, Background, Controls, Handle, Position } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { XIcon } from "lucide-react";
import { useTheme } from "next-themes";
import { ChatMessage } from "@/lib/store";

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
      <div className="p-4 text-xs text-foreground bg-card min-h-[70px] whitespace-pre-wrap">
        {data.content}
      </div>
      <div className={`p-2 bg-sidebar-accent/30 text-[10px] ${data.accentText || "text-muted-foreground"} font-mono border-t border-border flex items-center gap-1`}>
        {data.label.includes("Model Output") && <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${data.accentText ? "bg-current" : "bg-emerald-500"}`} />}
        {data.footer}
      </div>

      {data.source && (
        <Handle type="source" position={Position.Right} className="w-3 h-3 bg-foreground border-2 border-background" />
      )}
    </div>
  );
}

const nodeTypes = { workflow: WorkflowNode };

interface ChatWorkflowModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  messages: ChatMessage[];
}

export function ChatWorkflowModal({ open, onOpenChange, messages }: ChatWorkflowModalProps) {
  const { theme } = useTheme();
  
  // Ignore the initial welcome message from the system/assistant
  const history = messages.filter((m, i) => i !== 0);
  
  const nodes = [];
  const edges = [];
  let yPos = 100;
  let lastNodeId = null;
  
  for (let i = 0; i < history.length; i++) {
    const msg = history[i];
    
    if (msg.role === "user") {
      const userNodeId = `user-${msg.id}`;
      nodes.push({
        id: userNodeId,
        type: "workflow",
        position: { x: 50, y: yPos },
        data: {
          label: "User Input",
          description: "Incoming Request",
          content: msg.content.substring(0, 100) + (msg.content.length > 100 ? "..." : ""),
          footer: "Source: Chat UI",
          accent: "bg-sidebar-accent/50",
          target: lastNodeId !== null,
          source: true,
        }
      });
      
      if (lastNodeId) {
        edges.push({ id: `e-${lastNodeId}-${userNodeId}`, source: lastNodeId, target: userNodeId, animated: true, type: "smoothstep" });
      }
      lastNodeId = userNodeId;
      
      // Look ahead for the assistant response
      if (i + 1 < history.length && history[i+1].role === "assistant") {
        const asstMsg = history[i+1];
        const routerNodeId = `router-${asstMsg.id}`;
        const asstNodeId = `asst-${asstMsg.id}`;
        
        nodes.push({
          id: routerNodeId,
          type: "workflow",
          position: { x: 450, y: yPos },
          data: {
            label: "Kavach Semantic Router",
            description: "Intent & Complexity Classification",
            content: "Analyzing query to route to the most optimal on-premise model...",
            footer: "Execution: Local Backend",
            accent: "bg-primary/10",
            accentText: "text-primary",
            glow: "shadow-[0_0_15px_rgba(245,158,11,0.15)] border-primary/50",
            target: true,
            source: true,
          }
        });
        edges.push({ id: `e-${userNodeId}-${routerNodeId}`, source: userNodeId, target: routerNodeId, animated: true, type: "smoothstep" });
        
        const modelName = asstMsg.model || "llama3.2:1b";
        let modelDesc = "General reasoning & drafting";
        let accent = "bg-sidebar-accent/50";
        let accentText = "text-foreground";
        let glow = "";
        
        if (modelName.includes("coder")) {
          modelDesc = "Code Generation / Script Execution";
          accent = "bg-blue-500/10";
          accentText = "text-blue-500";
          glow = "shadow-[0_0_15px_rgba(59,130,246,0.15)] border-blue-500/50";
        } else if (modelName.includes("vl")) {
          modelDesc = "Vision Analysis / Image Understanding";
          accent = "bg-emerald-500/10";
          accentText = "text-emerald-500";
          glow = "shadow-[0_0_15px_rgba(16,185,129,0.15)] border-emerald-500/50";
        } else {
            accent = "bg-purple-500/10";
            accentText = "text-purple-500";
            glow = "shadow-[0_0_15px_rgba(168,85,247,0.15)] border-purple-500/50";
        }
        
        nodes.push({
          id: asstNodeId,
          type: "workflow",
          position: { x: 850, y: yPos },
          data: {
            label: `Selected: ${modelName}`,
            description: modelDesc,
            content: asstMsg.content.substring(0, 100) + (asstMsg.content.length > 100 ? "..." : ""),
            footer: "Status: Response Generated",
            accent,
            accentText,
            glow,
            target: true,
            source: true,
          }
        });
        edges.push({ id: `e-${routerNodeId}-${asstNodeId}`, source: routerNodeId, target: asstNodeId, animated: true, type: "smoothstep" });
        
        lastNodeId = asstNodeId;
        i++; // skip assistant message
      }
      yPos += 250;
    }
  }
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="!max-w-[100vw] sm:!max-w-[100vw] !w-screen !h-screen !rounded-none flex flex-col bg-background border-none p-0 overflow-hidden">
        <div className="p-6 border-b border-border bg-card shadow-sm z-20 relative flex items-center justify-between">
          <div>
            <DialogTitle className="text-xl font-bold text-foreground">Conversation Workflow Trace</DialogTitle>
            <p className="text-sm text-muted-foreground mt-1">Live visualization of semantic routing and model execution for this session.</p>
          </div>
          <DialogClose className="p-2 rounded-lg hover:bg-sidebar-accent text-muted-foreground transition-colors">
            <XIcon className="w-5 h-5" />
            <span className="sr-only">Close</span>
          </DialogClose>
        </div>
        
        <div className="flex-1 w-full h-full relative">
          {nodes.length > 0 ? (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              fitView
              fitViewOptions={{ padding: 0.2 }}
              className="bg-background"
              colorMode={theme === "dark" ? "dark" : "light"}
            >
              <Background gap={16} size={1} />
              <Controls />
            </ReactFlow>
          ) : (
            <div className="w-full h-full flex items-center justify-center text-muted-foreground">
              No workflow history available yet. Send a message to start tracing.
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
