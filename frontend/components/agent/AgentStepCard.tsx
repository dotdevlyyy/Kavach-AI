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
    <div className="mb-2 bg-white rounded-xl overflow-hidden shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-gray-100">
      {/* Header */}
      <div 
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className="p-1 rounded-md text-gray-500">
            <Icon className="w-4 h-4" />
          </div>
          <span className="font-medium text-sm text-gray-700">
            {config.label}
          </span>
          {!step.isComplete && (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-400" />
          )}
          {step.isComplete && (
            <span className="flex items-center gap-1 text-[10px] font-medium text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full border border-emerald-100">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
              Completed
            </span>
          )}
        </div>
        <div className="text-gray-400">
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </div>

      {/* Content Body */}
      {isExpanded && (
        <div className="px-4 py-3 border-t border-gray-100 bg-gray-50/50 text-sm text-gray-600 font-mono whitespace-pre-wrap">
          {step.content || <span className="text-gray-400 italic">Thinking...</span>}
        </div>
      )}
    </div>
  );
}
