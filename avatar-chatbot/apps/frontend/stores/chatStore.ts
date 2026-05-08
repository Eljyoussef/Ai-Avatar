import { create } from 'zustand';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

interface ChatState {
  messages: Message[];
  sessionId: string;
  addMessage: (msg: Message) => void;
  setSessionId: (id: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  sessionId: '',
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setSessionId: (id) => set({ sessionId: id }),
}));