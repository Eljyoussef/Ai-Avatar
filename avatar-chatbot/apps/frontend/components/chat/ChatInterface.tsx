'use client';

import { useState, useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { useChatStore } from '@/stores/chatStore';
import { wsService } from '@/services/websocket.service';

export function ChatInterface() {
  const { messages, addMessage, sessionId } = useChatStore();
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    wsService.on('connected', () => setIsConnected(true));
    wsService.on('disconnected', () => setIsConnected(false));
    wsService.on('text_response', (data: any) => {
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.text,
        timestamp: Date.now(),
      });
    });

    if (sessionId) {
      wsService.connect(sessionId);
    }

    return () => {
      wsService.disconnect();
    };
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: input,
      timestamp: Date.now(),
    });

    wsService.sendText(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="card flex flex-col h-[600px]">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">💬 Conversation</h2>
        <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 mb-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            <p className="text-4xl mb-4">🎙️</p>
            <p>Commencez à parler ou écrivez un message</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Écrivez votre message..."
          className="input flex-1"
          disabled={!isConnected}
        />
        <button onClick={handleSend} className="btn-primary" disabled={!isConnected}>
          ➤
        </button>
      </div>
    </div>
  );
}