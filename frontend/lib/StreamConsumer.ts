export type StreamEventType = 'metadata' | 'task_created' | 'step' | 'tool_result' | 'token' | 'done' | 'error';

export interface StreamEvent {
  type: StreamEventType;
  data: Record<string, unknown>;
}

export async function consumeSSEStream(
  url: string,
  body: unknown,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    });

    if (!response.ok) {
      let detail = response.statusText;
      try {
        const payload = (await response.json()) as { detail?: string };
        detail = payload.detail || detail;
      } catch {
        // Preserve status text when the server returns a non-JSON error.
      }
      throw new Error(`API Error: ${response.status} ${detail}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    if (!reader) return;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep the last incomplete line

      let currentEvent: string | null = null;

      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.substring(6).trim();
        } else if (line.startsWith('data:')) {
          const dataStr = line.substring(5).trim();
          if (currentEvent && dataStr) {
            try {
              const data = JSON.parse(dataStr);
              onEvent({ type: currentEvent as StreamEventType, data });
            } catch {
              console.error('Failed to parse SSE data', dataStr);
            }
          }
          currentEvent = null;
        }
      }
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") return;
    console.warn("Stream consumption failed:", error);
    onEvent({ type: 'error', data: { detail: (error as Error).message } });
  }
}

export async function uploadFiles(files: File[]): Promise<string[]> {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${apiBase}/api/files/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const payload = (await res.json()) as { detail?: string };
        detail = payload.detail || detail;
      } catch {
        // Preserve status text when the server returns a non-JSON error.
      }
      throw new Error(`Upload failed: ${res.status} ${detail}`);
    }
    const data = await res.json();
    if (!Array.isArray(data.files) || data.files.length !== files.length) {
      throw new Error('Upload failed: backend returned incomplete file metadata');
    }
    return data.files.map((file: { id: string }) => file.id);
  } catch (err) {
    console.error(err);
    throw err instanceof Error ? err : new Error('Upload failed');
  }
}
