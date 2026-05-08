type MessageHandler = (data: unknown) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(sessionId: string): void {
    this.sessionId = sessionId;
    const wsUrl = `ws://localhost:8000/ws/${sessionId}`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connected', { sessionId });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const type = data.type || 'message';
        this.emit(type, data);
        this.emit('*', data);
      } catch {
        // Binary data (audio)
        this.emit('audio', event.data);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.emit('disconnected', {});
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', { error });
    };
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.sessionId) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnecting... attempt ${this.reconnectAttempts}`);
        this.connect(this.sessionId!);
      }, 1000 * this.reconnectAttempts);
    }
  }

  on(event: string, handler: MessageHandler): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)!.push(handler);
  }

  off(event: string, handler: MessageHandler): void {
    const handlers = this.handlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) handlers.splice(index, 1);
    }
  }

  private emit(event: string, data: unknown): void {
    const handlers = this.handlers.get(event) || [];
    handlers.forEach(handler => handler(data));
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      if (data instanceof ArrayBuffer || data instanceof Uint8Array) {
        this.ws.send(data);
      } else {
        this.ws.send(JSON.stringify(data));
      }
    }
  }

  sendText(text: string): void {
    this.send({ type: 'chat', content: text });
  }

  sendAudio(chunk: ArrayBuffer): void {
    this.send(chunk);
  }

  sendInterrupt(): void {
    this.send({ type: 'interrupt' });
  }

  sendCommand(command: string, params?: Record<string, unknown>): void {
    this.send({ type: 'command', command, ...params });
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
    this.sessionId = null;
  }
}

export const wsService = new WebSocketService();