"use client";

import { useEffect, useState } from "react";
import { AgentOpsMonitor, type OpsServiceMetric, type OpsSignal } from "@/components/agents-ui/agent-ops-monitor";

interface HealthData { air_gapped: boolean | null; ollama: { status: string; latency_ms: number }; database: { status: string } }
interface ModelInfo { name: string; purpose: string; size_gb: number; installed: boolean; loaded: boolean; ready: boolean }

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    setError(null);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const [healthResponse, modelsResponse] = await Promise.all([fetch(`${apiBase}/api/health`), fetch(`${apiBase}/api/models`)]);
      if (!healthResponse.ok || !modelsResponse.ok) throw new Error("Unable to retrieve operational status");
      setHealth(await healthResponse.json() as HealthData);
      setModels((await modelsResponse.json() as { models?: ModelInfo[] }).models ?? []);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to retrieve operational status"); }
  };

  useEffect(() => { void refresh(); }, []);
  const loaded = models.filter((model) => model.loaded);
  const signals: OpsSignal[] = health ? [
    { id: "backend", title: "Backend service", status: "healthy", detail: "Health endpoint responded.", lastUpdated: "Latest check" },
    { id: "ollama", title: "Local model host", status: health.ollama.status === "connected" ? "healthy" : "warning", detail: health.ollama.status, lastUpdated: `${health.ollama.latency_ms} ms` },
    { id: "air-gap", title: "Air-gap status", status: health.air_gapped === true ? "healthy" : health.air_gapped === false ? "critical" : "warning", detail: health.air_gapped === true ? "No external traffic reported." : "Network verification required." },
  ] : [{ id: "status", title: "Status unavailable", status: "warning", detail: error ?? "Loading services..." }];
  const metrics: OpsServiceMetric[] = [
    { label: "Loaded models", value: String(loaded.length), threshold: "Local inventory", trend: "stable" },
    { label: "Allocated VRAM", value: `${loaded.reduce((total, model) => total + model.size_gb, 0).toFixed(1)} GB`, threshold: "Loaded models only", trend: "stable" },
    { label: "Database", value: health?.database.status ?? "Unknown", threshold: "Ready", trend: "stable" },
  ];
  return <div className="mx-auto w-full max-w-6xl p-4 sm:p-8"><AgentOpsMonitor environment="Kavach AI local workbench" uptime={health ? "Live status" : "Checking"} signals={signals} metrics={metrics} incidents={models.filter((model) => !model.ready).map((model) => ({ id: model.name, timestamp: "Inventory", summary: `${model.name}: ${model.purpose}`, actionNeeded: model.installed ? "Load model" : "Install model" }))} /></div>;
}
