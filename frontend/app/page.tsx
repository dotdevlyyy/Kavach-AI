export default function DashboardPage() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6 text-foreground">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-card border border-border rounded-xl">
          <h2 className="text-lg font-semibold text-primary mb-2">GPU VRAM Allocated</h2>
          <p className="text-3xl font-bold text-foreground">4.1 / 8 GB</p>
          <div className="w-full bg-sidebar-accent h-2 mt-4 rounded-full overflow-hidden">
            <div className="bg-primary w-[51%] h-full" />
          </div>
        </div>

        <div className="p-6 bg-card border border-border rounded-xl">
          <h2 className="text-lg font-semibold text-emerald-500 mb-2">Network Sovereignty</h2>
          <p className="text-3xl font-bold text-foreground">100% Secure</p>
          <p className="text-sm text-muted-foreground mt-2">0 external packets detected</p>
        </div>

        <div className="p-6 bg-card border border-border rounded-xl">
          <h2 className="text-lg font-semibold text-purple-400 mb-2">Active Models</h2>
          <ul className="text-sm text-muted-foreground mt-2 space-y-2 font-mono">
            <li>🟢 Llama 3.2 (1B)</li>
            <li>🟢 Qwen2.5-Coder (1.5B)</li>
            <li>🟢 Qwen2.5-VL (3B)</li>
          </ul>
        </div>
      </div>

      <div className="mt-8 p-6 bg-card border border-border rounded-xl">
        <p className="text-muted-foreground">
          // @Pritam: Dashboard widgets go here. The grid is already set up for you.
        </p>
      </div>
    </div>
  );
}
