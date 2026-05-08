import { useEffect, useRef, useCallback, useState } from 'react';

interface UseWebRTCReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  sendAudio: (chunk: ArrayBuffer) => void;
  sendText: (text: string) => void;
  interrupt: () => void;
}

export function useWebRTC(sessionId: string): UseWebRTCReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'audio_chunk') {
        // Convert hex back to bytes and play
        const audioBytes = new Uint8Array(
          (data.audio as string).match(/.{1,2}/g)!
            .map(byte => parseInt(byte, 16))
        );
        
        const audioContext = new AudioContext();
        audioContext.decodeAudioData(audioBytes.buffer, (buffer) => {
          const source = audioContext.createBufferSource();
          source.buffer = buffer;
          source.connect(audioContext.destination);
          source.start();
        });
      }

      if (data.type === 'text_response') {
        const event = new CustomEvent('chat-message', {
          detail: { role: 'assistant', content: data.text }
        });
        window.dispatchEvent(event);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };
  }, [sessionId]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    setIsConnected(false);
  }, []);

  const sendAudio = useCallback((chunk: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(chunk);
    }
  }, []);

  const sendText = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'chat', content: text }));
    }
  }, []);

  const interrupt = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'interrupt' }));
    }
  }, []);

  return { isConnected, connect, disconnect, sendAudio, sendText, interrupt };
}