export class StreamConsumer {
  private url: string;
  private onToken: (token: string) => void;
  private onStep: (step: any) => void;
  private onDone: () => void;
  private onError: (error: Error) => void;

  constructor(
    url: string,
    onToken: (token: string) => void,
    onStep: (step: any) => void,
    onDone: () => void,
    onError: (error: Error) => void
  ) {
    this.url = url;
    this.onToken = onToken;
    this.onStep = onStep;
    this.onDone = onDone;
    this.onError = onError;
  }

  async start(payload: any) {
    try {
      const response = await fetch(this.url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("ReadableStream not supported");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const event of events) {
          if (!event.trim()) continue;
          
          const lines = event.split("\n");
          let eventType = "message";
          let data = "";

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              data = line.slice(6);
            }
          }

          if (!data) continue;

          try {
            if (eventType === "token") {
              const parsed = JSON.parse(data);
              this.onToken(parsed.text || "");
            } else if (eventType === "step") {
              this.onStep(JSON.parse(data));
            } else if (eventType === "done") {
              this.onDone();
            }
          } catch (e) {
            console.error("Error parsing SSE data", e, data);
          }
        }
      }
      this.onDone();
    } catch (e) {
      this.onError(e instanceof Error ? e : new Error(String(e)));
    }
  }
}
