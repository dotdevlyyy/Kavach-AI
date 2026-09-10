"use client";

import { useEffect, useState } from "react";
import { AgentOpsMonitor, type OpsServiceMetric, type OpsSignal } from "@/components/agents-ui/agent-ops-monitor";

interface ModelInfo { name: string; size_gb: number; parameters: string; installed?: boolean; loaded?: boolean; ready?: boolean }

export default function SettingsPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const refresh = async () => {
    setError(null);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiBase}/api/models`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setModels((await response.json() as { models?: ModelInfo[] }).models ?? []);
    } catch (cause) { setModels([]); setError(cause instanceof Error ? cause.message : "Unable to fetch models"); }
  };
  useEffect(() => { void refresh(); }, []);
  const signals: OpsSignal[] = models.length ? models.map((model) => ({ id: model.name, title: model.name, status: model.ready ? "healthy" : model.installed ? "warning" : "critical", detail: `${model.parameters} · ${model.size_gb} GB` })) : [{ id: "models", title: "Model inventory", status: error ? "warning" : "healthy", detail: error ?? "No models reported by the backend." }];
  const metrics: OpsServiceMetric[] = [{ label: "Installed models", value: String(models.filter((model) => model.installed).length), threshold: "Backend inventory", trend: "stable" }, { label: "Loaded models", value: String(models.filter((model) => model.loaded).length), threshold: "On demand", trend: "stable" }, { label: "Available models", value: String(models.length), threshold: "Local host", trend: "stable" }];
  return <div className="mx-auto w-full max-w-6xl p-4 sm:p-8"><AgentOpsMonitor environment="Model configuration" uptime="Local inventory" signals={signals} metrics={metrics} incidents={[]} /></div>;
}
