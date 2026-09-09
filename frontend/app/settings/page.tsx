"use client";

import { useEffect, useState } from "react";
import { Cpu } from "lucide-react";

interface ModelInfo {
  name: string;
  size_gb: number;
  parameters: string; // parameter_size as string (e.g., "1B")
}

export default function SettingsPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${apiBase}/api/models`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      // Expected shape: { models: ModelInfo[] }
      setModels(data.models ?? []);
    } catch (e: any) {
      setError(e?.message ?? "Unable to fetch models");
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-foreground mb-6">Model Configuration</h1>

      {loading ? (
        // Loading placeholders using animate-pulse
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="p-4 bg-card border border-border rounded-xl animate-pulse h-32"
            />
          ))}
        </div>
      ) : error ? (
        <div className="p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded-xl">
          <p className="font-medium">Error loading models: {error}</p>
        </div>
      ) : models.length === 0 ? (
        <p className="text-muted-foreground">No models available.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {models.map((model) => (
            <div
              key={model.name}
              className="p-4 bg-card border border-border rounded-xl hover:border-primary/50 transition-colors"
            >
              <div className="flex items-center mb-2">
                <Cpu className="w-5 h-5 text-primary mr-2" />
                <h2 className="text-lg font-semibold text-primary">{model.name}</h2>
              </div>
              <p className="text-sm text-foreground">
                Size: {model.size_gb} GB
              </p>
              <p className="text-sm text-foreground">
                Parameters: {model.parameters}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
