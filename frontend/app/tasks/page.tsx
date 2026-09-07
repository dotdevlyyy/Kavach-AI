export default function TasksPage() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8 text-foreground">Task History</h1>
      
      <div className="p-6 bg-card border border-border rounded-xl">
        <p className="text-muted-foreground">
          // @Pritam: Wire up `GET /api/agent/tasks` to show past agent runs, token usage, and latency.
        </p>
      </div>
    </div>
  );
}
