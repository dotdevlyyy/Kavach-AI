export type StreamEventType = 'metadata' | 'task_created' | 'step' | 'tool_result' | 'token' | 'done' | 'error';

export interface StreamEvent {
  type: StreamEventType;
  data: any;
}

export async function consumeSSEStream(
  url: string,
  body: any,
  onEvent: (event: StreamEvent) => void
) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
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
            } catch (e) {
              console.error('Failed to parse SSE data', dataStr);
            }
          }
          currentEvent = null;
        }
      }
    }
  } catch (error) {
    console.warn("Stream consumption failed:", error);
    onEvent({ type: 'error', data: { detail: (error as Error).message } });
  }
}

export async function uploadFiles(files: File[]): Promise<string[]> {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  try {
    const res = await fetch('http://localhost:8000/api/files/upload', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Upload failed');
    const data = await res.json();
    return data.files.map((f: any) => f.id);
  } catch (err) {
    console.error(err);
    return [];
  }
}
