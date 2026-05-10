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
  isRecording: boolean;
  isSpeaking: boolean;
  selectedAccent: string;
  gender: 'male' | 'female' | 'neutral';
  avatarEnabled: boolean;
  
  addMessage: (msg: Message) => void;
  setSessionId: (id: string) => void;
  setIsRecording: (recording: boolean) => void;
  setIsSpeaking: (speaking: boolean) => void;
  setSelectedAccent: (accent: string) => void;
  setGender: (gender: 'male' | 'female' | 'neutral') => void;
  setAvatarEnabled: (enabled: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  sessionId: '',
  isRecording: false,
  isSpeaking: false,
  selectedAccent: 'fr-FR',
  gender: 'neutral',
  avatarEnabled: false,
  
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setSessionId: (id) => set({ sessionId: id }),
  setIsRecording: (recording) => set({ isRecording: recording }),
  setIsSpeaking: (speaking) => set({ isSpeaking: speaking }),
  setSelectedAccent: (accent) => set({ selectedAccent: accent }),
  setGender: (gender) => set({ gender }),
  setAvatarEnabled: (enabled) => set({ avatarEnabled: enabled }),
}));