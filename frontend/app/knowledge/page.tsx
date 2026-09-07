export default function KnowledgeBasePage() {
  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-foreground">Knowledge Base Manager</h1>
        <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
          Upload SOP Document
        </button>
      </div>
      
      <div className="p-6 bg-card border border-border rounded-xl">
        <p className="text-muted-foreground">
          // @Pritam: Wire up the `GET /api/knowledge/documents` list here to show indexed MRPL SOPs and Refinery guidelines.
        </p>
      </div>
    </div>
  );
}
