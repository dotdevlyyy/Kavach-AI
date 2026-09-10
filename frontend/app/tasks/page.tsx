"use client";

import { useEffect, useState } from "react";
import { Clock, AlertCircle, RefreshCw } from "lucide-react";
import { AgentTaskQueue, type AgentTask } from "@/components/agents-ui/agent-task-queue";

interface AgentTaskItem {
  id: string;
  description: string;
  status: string;
  total_steps: number;
  created_at: string;
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<AgentTaskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${apiBase}/api/agent/tasks`);
      if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to connect to backend";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const queueTasks: AgentTask[] = tasks.map((task) => ({
    id: task.id,
    title: task.description,
    status: task.status === "executing" ? "running" : task.status === "cancelled" ? "blocked" : task.status as AgentTask["status"],
    progress: task.status === "completed" ? 100 : undefined,
    createdAt: task.created_at,
    updatedLabel: new Date(task.created_at).toLocaleString(),
    checkpoints: Array.from({ length: task.total_steps }, (_, index) => ({
      id: `${task.id}-${index + 1}`,
      title: `Step ${index + 1}`,
      status: task.status === "completed" ? "completed" : "pending",
    })),
  }));

  return (
    <div className="h-[calc(100dvh-4rem)] min-h-0 flex flex-col overflow-hidden">
      <div className="shrink-0 flex flex-wrap items-center justify-between gap-3 border-b border-border/50 p-4 sm:px-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Task History</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Recorded multi-step ReAct agent executions and deliverables
          </p>
        </div>
        <button
          onClick={fetchTasks}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-sidebar-accent border border-border rounded-lg text-sm text-foreground hover:bg-sidebar-accent/80 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-8">
      {error && (
        <div className="p-4 mb-6 bg-destructive/10 border border-destructive/20 text-destructive rounded-xl flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>Could not retrieve tasks from {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}: {error}</span>
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-muted-foreground">Loading task history...</div>
      ) : tasks.length === 0 ? (
        <div className="p-12 bg-card border border-border rounded-xl text-center">
          <Clock className="w-10 h-10 text-muted-foreground mx-auto mb-3 opacity-50" />
          <h3 className="text-lg font-medium text-foreground mb-1">No agent tasks recorded yet</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            Start a task in the Chat workbench using keywords like &quot;plan&quot; or &quot;execute&quot; to see autonomous agent steps recorded here.
          </p>
        </div>
      ) : (
        <AgentTaskQueue tasks={queueTasks} isProcessing={tasks.some((task) => task.status === "executing")} />
      )}
      </div>
    </div>
  );
}
