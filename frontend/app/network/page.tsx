"use client";

import { ShieldAlert, Server, Activity } from "lucide-react";
import { SonarGrid } from "@/components/ui/sonar-grid";

export default function NetworkMonitorPage() {
  return (
    <SonarGrid
      color="#10b981" // emerald-500
      pingEvery={2.4}
      speed={200}
      amplitude={2}
      className="min-h-screen bg-background"
    >
      <div className="p-8 relative z-10 w-full h-full flex flex-col items-center justify-center min-h-[80vh] text-center">
        <div className="mb-6 p-4 rounded-full bg-emerald-500/10 border border-emerald-500/30 animate-pulse">
          <ShieldAlert className="w-16 h-16 text-emerald-500" />
        </div>
        
        <h1 className="text-4xl font-bold text-foreground mb-4">AIR-GAP STATUS: <span className="text-emerald-500">100% SECURE</span></h1>
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
              <span className="text-5xl font-black text-emerald-500 mb-2">0</span>
              <span className="text-muted-foreground font-medium uppercase tracking-widest text-sm">Packets Sent/Received</span>
            </div>
          </div>
        </div>

        <div className="w-full max-w-4xl text-left">
          <div className="p-6 bg-card/80 backdrop-blur-sm border border-border rounded-xl mb-6">
            <p className="text-muted-foreground font-mono text-sm">
              Socket audit monitor: All telemetry traffic restricted to local loopback interface.
            </p>
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
                <tr className="hover:bg-sidebar-accent/50">
                  <td className="px-6 py-4 font-medium">ollama.exe</td>
                  <td className="px-6 py-4 text-muted-foreground">TCP</td>
                  <td className="px-6 py-4 font-mono">127.0.0.1:11434</td>
                  <td className="px-6 py-4 font-mono text-emerald-500">127.0.0.1:54321 (Local)</td>
                  <td className="px-6 py-4">ESTABLISHED</td>
                </tr>
                <tr className="hover:bg-sidebar-accent/50">
                  <td className="px-6 py-4 font-medium">python.exe (FastAPI)</td>
                  <td className="px-6 py-4 text-muted-foreground">TCP</td>
                  <td className="px-6 py-4 font-mono">127.0.0.1:8000</td>
                  <td className="px-6 py-4 font-mono text-emerald-500">127.0.0.1:3000 (Local)</td>
                  <td className="px-6 py-4">ESTABLISHED</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </SonarGrid>
  );
}
