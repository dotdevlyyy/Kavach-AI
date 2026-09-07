export default function SettingsPage() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8 text-foreground">System Settings</h1>
      
      <div className="p-6 bg-card border border-border rounded-xl">
        <h2 className="text-xl font-semibold mb-4 text-primary">Model Configuration</h2>
        <p className="text-muted-foreground mb-4">
          {/* @Pritam: Wire up to GET /api/models to show Ollama model management, VRAM limits, etc. */}
          Configured models: llama3.2:1b (General), qwen2.5-coder:1.5b (Code), qwen2.5vl:3b (Vision/OCR).
        </p>
      </div>
    </div>
  );
}
