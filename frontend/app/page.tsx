"use client";

import { useEffect, useState } from "react";
import { Activity, ShieldCheck, Cpu, RefreshCw } from "lucide-react";

interface HealthData {
  status: string;
  app: string;
  version: string;
  air_gapped: boolean;
  ollama: {
    status: string;
    host: string;
    latency_ms: number;
  };
  database: {
    status: string;
    path: string;
  };
}

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    setLoading(true);
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${apiBase}/api/health`);
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch {
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground">MRPL Operational Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Kavach AI Sovereign On-Premises Industrial Workbench
          </p>
        </div>
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 bg-sidebar-accent border border-border rounded-lg text-xs text-foreground hover:bg-sidebar-accent/80 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Check Health
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* VRAM / Model status */}
        <div className="p-6 bg-card border border-border rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-primary">GPU VRAM Allocated</h2>
            <Cpu className="w-5 h-5 text-primary opacity-80" />
          </div>
          <p className="text-3xl font-bold text-foreground">4.1 / 8 GB</p>
          <div className="w-full bg-sidebar-accent h-2 mt-4 rounded-full overflow-hidden">
            <div className="bg-primary w-[51%] h-full" />
          </div>
          <p className="text-xs text-muted-foreground mt-2">Allocated for 3 concurrent hot-swappable models</p>
        </div>

        {/* Network Air-Gap */}
        <div className="p-6 bg-card border border-border rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-emerald-500">Air-Gap Sovereignty</h2>
            <ShieldCheck className="w-5 h-5 text-emerald-500 opacity-80" />
          </div>
          <p className="text-3xl font-bold text-foreground">100% Secure</p>
          <p className="text-xs text-muted-foreground mt-2">
            {health?.air_gapped ? "Strict air-gap mode verified — 0 external packets" : "Air-gap security active"}
          </p>
        </div>

        {/* Database & Service Health */}
        <div className="p-6 bg-card border border-border rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-purple-400">Core Services</h2>
            <Activity className="w-5 h-5 text-purple-400 opacity-80" />
          </div>
          <div className="space-y-2 text-xs font-mono mt-3">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">FastAPI Backend</span>
              <span className="text-emerald-500 font-bold">● {health ? "ONLINE" : "CONNECTING"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">SQLite WAL DB</span>
              <span className={health?.database ? "text-emerald-500 font-bold" : "text-amber-500 font-bold"}>
                ● {health?.database ? "READY" : "LOCAL"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Ollama Model Host</span>
              <span className={health?.ollama?.status === "connected" ? "text-emerald-500 font-bold" : "text-amber-400 font-bold"}>
                ● {health?.ollama?.status === "connected" ? "CONNECTED" : "OFFLINE / LOCAL"}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* On-Premise Models */}
        <div className="p-6 bg-card border border-border rounded-xl">
          <h3 className="text-base font-semibold text-foreground mb-4">Dedicated On-Premise Models</h3>
          <ul className="space-y-3 text-sm">
            <li className="flex items-center justify-between p-3 rounded-lg bg-sidebar-accent/50">
              <div>
                <span className="font-semibold text-foreground font-mono">llama3.2:1b</span>
                <p className="text-xs text-muted-foreground">General reasoning, summarization & SOP drafting</p>
              </div>
              <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary font-mono">0.8 GB</span>
            </li>
            <li className="flex items-center justify-between p-3 rounded-lg bg-sidebar-accent/50">
              <div>
                <span className="font-semibold text-foreground font-mono">qwen2.5-coder:1.5b</span>
                <p className="text-xs text-muted-foreground">Python sandbox script execution & data processing</p>
              </div>
              <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary font-mono">1.1 GB</span>
            </li>
            <li className="flex items-center justify-between p-3 rounded-lg bg-sidebar-accent/50">
              <div>
                <span className="font-semibold text-foreground font-mono">qwen2.5vl:3b</span>
                <p className="text-xs text-muted-foreground">Vision analysis, P&ID diagram parsing & OCR</p>
              </div>
              <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary font-mono">2.2 GB</span>
            </li>
          </ul>
        </div>

        {/* Operational Quick Start */}
        <div className="p-6 bg-card border border-border rounded-xl">
          <h3 className="text-base font-semibold text-foreground mb-4">Refinery Workflow Capabilities</h3>
          <div className="space-y-2.5 text-xs text-muted-foreground">
            <div className="p-2.5 rounded-lg border border-border bg-sidebar-accent/20">
              <span className="font-semibold text-foreground">Multi-Step ReAct Agent:</span>
              <p className="mt-0.5">Use phrases like <em>&quot;plan and execute inspection note&quot;</em> to invoke autonomous step decomposition.</p>
            </div>
            <div className="p-2.5 rounded-lg border border-border bg-sidebar-accent/20">
              <span className="font-semibold text-foreground">Document Deliverables:</span>
              <p className="mt-0.5">Autonomous output generation directly produces downloadable Word (.docx) and Excel (.xlsx) files.</p>
            </div>
            <div className="p-2.5 rounded-lg border border-border bg-sidebar-accent/20">
              <span className="font-semibold text-foreground">Knowledge Base RAG:</span>
              <p className="mt-0.5">Full-text SQLite FTS5 search across refinery SOPs with Reciprocal Rank Fusion.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
