"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Clock, AlertCircle, RefreshCw } from "lucide-react";

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

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
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
        <div className="overflow-hidden rounded-xl border border-border bg-card">
          <table className="w-full text-sm text-left">
            <thead className="bg-sidebar-accent text-muted-foreground uppercase text-xs">
              <tr>
                <th className="px-6 py-3">Task Description</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Steps</th>
                <th className="px-6 py-3">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border text-foreground">
              {tasks.map((task) => (
                <tr key={task.id} className="hover:bg-sidebar-accent/40 transition-colors">
                  <td className="px-6 py-4 font-medium max-w-md truncate">{task.description}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                        task.status === "completed"
                          ? "bg-emerald-500/10 text-emerald-500"
                          : task.status === "executing"
                          ? "bg-blue-500/10 text-blue-400"
                          : "bg-amber-500/10 text-amber-400"
                      }`}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {task.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono text-muted-foreground">{task.total_steps}</td>
                  <td className="px-6 py-4 text-xs text-muted-foreground">
                    {new Date(task.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
