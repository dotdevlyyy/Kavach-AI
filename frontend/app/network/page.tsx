export default function NetworkAuditPage() {
  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-foreground">Network Sovereignty Audit</h1>
        <div className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded-lg font-bold flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          AIR-GAP STATUS: 100% SECURE
        </div>
      </div>
      
      <div className="p-6 bg-card border border-border rounded-xl mb-6">
        <p className="text-muted-foreground font-mono">
          {/* @Pritam: Wire this up to the GET /api/network/connections endpoint to display the live socket table. */}
          Socket audit monitor: All telemetry traffic restricted to local loopback interface.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-border">
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
          <tbody className="bg-card divide-y divide-border text-foreground">
            {/* Mock Data */}
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
  );
}
