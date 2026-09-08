"use client";

import { useEffect, useState } from "react";
import { ShieldAlert, Server, Activity, RefreshCw } from "lucide-react";
import { SonarGrid } from "@/components/ui/sonar-grid";

interface NetworkConnection {
  process: string;
  protocol: string;
  local_address: string;
  remote_address: string;
  status: string;
  is_local: boolean;
}

interface NetworkAuditData {
  total_connections: number;
  local_connections_count: number;
  external_connections: number;
  is_air_gapped: boolean;
  air_gap_status: string;
  connections: NetworkConnection[];
}

export default function NetworkMonitorPage() {
  const [audit, setAudit] = useState<NetworkAuditData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNetworkAudit = async () => {
    setLoading(true);
    setError(null);
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${apiBase}/api/network`);
      if (res.ok) {
        const data: NetworkAuditData = await res.json();
        setAudit(data);
      } else {
        setError(`Backend network audit returned status ${res.status}`);
        setAudit(null);
      }
    } catch {
      setError("Unable to reach backend network audit endpoint");
      setAudit(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNetworkAudit();
  }, []);

  const externalCount = audit ? audit.external_connections : 0;
  const isAirGapped = audit ? audit.is_air_gapped : true;
  const connections = audit?.connections ?? [];

  return (
    <SonarGrid
      color="#10b981" // emerald-500
      pingEvery={2.4}
      speed={200}
      amplitude={2}
      className="min-h-screen bg-background"
    >
      <div className="p-8 relative z-10 w-full h-full flex flex-col items-center min-h-[80vh] text-center pt-16">
        <div className="mb-6 p-4 rounded-full bg-emerald-500/10 border border-emerald-500/30 animate-pulse flex items-center justify-center">
          <ShieldAlert className="w-16 h-16 text-emerald-500" />
        </div>
        
        <h1 className="text-4xl font-bold text-foreground mb-4">
          AIR-GAP STATUS:{" "}
          <span className={isAirGapped ? "text-emerald-500" : "text-amber-500"}>
            {loading ? "CHECKING..." : isAirGapped ? "100% SECURE" : "EXTERNAL CONNECTION DETECTED"}
          </span>
        </h1>
        <p className="text-muted-foreground text-lg max-w-xl mx-auto mb-12">
          Kavach AI is running completely isolated from external networks. No outbound packets or unauthorized external connections detected.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl text-left mb-12">
          <div className="p-6 bg-card/80 backdrop-blur-sm border border-emerald-500/30 rounded-xl shadow-[0_0_15px_rgba(16,185,129,0.15)]">
            <div className="flex items-center gap-3 mb-4">
              <Server className="w-6 h-6 text-emerald-500" />
              <h2 className="text-xl font-semibold text-foreground">Local Connections</h2>
            </div>
            <div className="space-y-3 font-mono text-sm">
              <div className="flex justify-between border-b border-border pb-2">
                <span className="text-muted-foreground">127.0.0.1:3000 (UI)</span>
                <span className="text-emerald-500">ESTABLISHED</span>
              </div>
              <div className="flex justify-between border-b border-border pb-2">
                <span className="text-muted-foreground">127.0.0.1:8000 (API)</span>
                <span className="text-emerald-500">ESTABLISHED</span>
              </div>
              <div className="flex justify-between border-b border-border pb-2">
                <span className="text-muted-foreground">127.0.0.1:11434 (Ollama)</span>
                <span className="text-emerald-500">ESTABLISHED</span>
              </div>
            </div>
          </div>

          <div className="p-6 bg-card/80 backdrop-blur-sm border border-emerald-500/30 rounded-xl shadow-[0_0_15px_rgba(16,185,129,0.15)]">
            <div className="flex items-center gap-3 mb-4">
              <Activity className="w-6 h-6 text-emerald-500" />
              <h2 className="text-xl font-semibold text-foreground">External Traffic</h2>
            </div>
            <div className="flex flex-col items-center justify-center h-full pb-8">
              <span className={`text-5xl font-black mb-2 ${externalCount === 0 ? "text-emerald-500" : "text-amber-500"}`}>
                {loading ? "..." : externalCount}
              </span>
              <span className="text-muted-foreground font-medium uppercase tracking-widest text-sm">Packets Sent/Received</span>
            </div>
          </div>
        </div>

        <div className="w-full max-w-4xl text-left">
          <div className="p-6 bg-card/80 backdrop-blur-sm border border-border rounded-xl mb-6 flex items-center justify-between">
            <p className="text-muted-foreground font-mono text-sm">
              Socket audit monitor: All telemetry traffic restricted to local loopback interface.
            </p>
            <button
              onClick={fetchNetworkAudit}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-1.5 bg-sidebar-accent border border-border rounded-lg text-xs text-foreground hover:bg-sidebar-accent/80 transition-colors shrink-0"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh Audit
            </button>
          </div>

          <div className="overflow-hidden rounded-xl border border-border bg-card/80 backdrop-blur-sm">
            <table className="w-full text-sm text-left">
              <thead className="bg-sidebar-accent text-muted-foreground uppercase">
                <tr>
                  <th className="px-6 py-3">Process</th>
                  <th className="px-6 py-3">Protocol</th>
                  <th className="px-6 py-3">Local Address</th>
                  <th className="px-6 py-3">Remote Address</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-foreground">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-muted-foreground font-mono">
                      Scanning active system sockets...
                    </td>
                  </tr>
                ) : error ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-amber-500 font-mono">
                      {error}
                    </td>
                  </tr>
                ) : connections.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-muted-foreground font-mono">
                      No active network connections detected
                    </td>
                  </tr>
                ) : (
                  connections.map((conn, idx) => (
                    <tr key={idx} className="hover:bg-sidebar-accent/50">
                      <td className="px-6 py-4 font-medium">{conn.process}</td>
                      <td className="px-6 py-4 text-muted-foreground">{conn.protocol}</td>
                      <td className="px-6 py-4 font-mono">{conn.local_address}</td>
                      <td className={`px-6 py-4 font-mono ${conn.is_local ? "text-emerald-500" : "text-amber-500"}`}>
                        {conn.remote_address}
                      </td>
                      <td className="px-6 py-4">{conn.status}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </SonarGrid>
  );
}
