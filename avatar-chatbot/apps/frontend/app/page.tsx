'use client';

import { ChatInterface } from '@/components/chat/ChatInterface';
import { VoiceControls } from '@/components/audio/VoiceControls';
import { AccentSelector } from '@/components/settings/AccentSelector';
import { SettingsPanel } from '@/components/settings/SettingsPanel';
import { AvatarDisplay } from '@/components/avatar/AvatarDisplay';
import { useChatStore } from '@/stores/chatStore';

export default function Home() {
  const { sessionId } = useChatStore();

  return (
    <main className="min-h-screen bg-dark-950">
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        {/* Header */}
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-500 to-blue-300 bg-clip-text text-transparent">
              🎙️ Avatar Chatbot
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              Assistant vocal français multi-accents
            </p>
          </div>
          <div className="text-sm text-gray-500">
            Session: {sessionId?.slice(0, 8)}...
          </div>
        </header>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Avatar + Voice */}
          <div className="lg:col-span-2 space-y-6">
            <AvatarDisplay />
            <VoiceControls />
          </div>

          {/* Right Column - Chat + Settings */}
          <div className="space-y-6">
            <ChatInterface />
            <AccentSelector />
            <SettingsPanel />
          </div>
        </div>
      </div>
    </main>
  );
}