"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Loader2, Target, Wrench, Eye, Lightbulb } from "lucide-react";

export type AgentStepType = "plan" | "act" | "observe" | "reflect";

export interface AgentStep {
  id: string;
  type: AgentStepType;
  content: string;
  isComplete: boolean;
}

interface AgentStepCardProps {
  step: AgentStep;
}

export function AgentStepCard({ step }: AgentStepCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const getStepConfig = (type: AgentStepType) => {
    switch (type) {
      case "plan":
        return { icon: Target, label: "Plan", color: "text-blue-400", bg: "bg-blue-400/10" };
      case "act":
        return { icon: Wrench, label: "Action", color: "text-amber-500", bg: "bg-amber-500/10" };
      case "observe":
        return { icon: Eye, label: "Observation", color: "text-emerald-500", bg: "bg-emerald-500/10" };
      case "reflect":
        return { icon: Lightbulb, label: "Reflection", color: "text-purple-400", bg: "bg-purple-400/10" };
    }
  };

  const config = getStepConfig(step.type);
  const Icon = config.icon;

  return (
    <div className="mb-4 bg-card border border-border rounded-lg overflow-hidden shadow-sm">
      {/* Header */}
      <div 
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-sidebar-accent/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className={`p-1.5 rounded-md ${config.bg} ${config.color}`}>
            <Icon className="w-4 h-4" />
          </div>
          <span className="font-semibold text-sm text-card-foreground">
            {config.label}
          </span>
          {!step.isComplete && (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground" />
          )}
        </div>
        <div className="text-muted-foreground">
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </div>

      {/* Content Body */}
      {isExpanded && (
        <div className="px-4 py-3 border-t border-border bg-sidebar-accent/30 text-sm text-card-foreground/90 font-mono whitespace-pre-wrap">
          {step.content || <span className="text-muted-foreground italic">Thinking...</span>}
        </div>
      )}
    </div>
  );
}
