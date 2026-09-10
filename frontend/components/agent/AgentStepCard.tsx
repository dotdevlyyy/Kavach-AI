"use client";

import { Check, ChevronDown, Circle, FileText, Lightbulb, Pencil, X } from "lucide-react";
import { useEffect, useState } from "react";

export type AgentStepType = "plan" | "act" | "observe" | "reflect";

export interface AgentStep {
  id: string;
  type: AgentStepType;
  content: string;
  isComplete: boolean;
  isFailed?: boolean;
}

const icons = { plan: Lightbulb, act: Pencil, observe: FileText, reflect: Circle };

export function AgentActivity({ steps, status }: { steps: AgentStep[]; status: "working" | "complete" | "failed" }) {
  const [open, setOpen] = useState(status === "working");
  useEffect(() => {
    setOpen(status === "working");
  }, [status]);
  const failedStep = steps.find((step) => step.isFailed);
  const summary = status === "working" ? "Working through it..." : status === "failed" ? `Failed at step ${failedStep?.id || "?"}` : `Completed ${steps.length} ${steps.length === 1 ? "step" : "steps"}`;

  return (
    <section className="w-full px-1 py-2 text-sm" aria-busy={status === "working"}>
      <button type="button" aria-expanded={open} onClick={() => setOpen((value) => !value)} className="flex min-h-7 items-center gap-1.5 text-left font-medium text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
        <span>{summary}</span>
        {status !== "working" && <ChevronDown className={`size-3.5 transition-transform ${open ? "rotate-180" : ""}`} aria-hidden />}
      </button>
      {open && <div className="mt-2 space-y-1.5" role="list">
        {steps.map((step) => {
          const Icon = step.isFailed ? X : step.isComplete ? Check : icons[step.type];
          return <div key={step.id} className="flex min-w-0 items-center gap-2.5" role="listitem">
            <Icon className={`size-4 shrink-0 ${step.isFailed ? "text-destructive" : step.isComplete ? "text-muted-foreground" : "animate-pulse text-muted-foreground"}`} aria-hidden />
            <span title={step.content || step.type} className={`min-w-0 truncate font-medium ${step.isFailed ? "text-destructive" : "text-foreground"}`}>{step.content || step.type}</span>
          </div>;
        })}
      </div>}
    </section>
  );
}
