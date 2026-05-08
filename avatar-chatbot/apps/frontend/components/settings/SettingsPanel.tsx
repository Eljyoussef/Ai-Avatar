'use client';

import { useChatStore } from '@/stores/chatStore';
import { wsService } from '@/services/websocket.service';

export function SettingsPanel() {
  const { avatarEnabled, setAvatarEnabled } = useChatStore();

  const toggleAvatar = () => {
    const newState = !avatarEnabled;
    setAvatarEnabled(newState);
    wsService.sendCommand(newState ? 'avatar_enable' : 'avatar_disable');
  };

  return (
    <div className="card space-y-4">
      <h2 className="text-lg font-semibold">⚙️ Paramètres</h2>

      <div className="flex items-center justify-between">
        <span>Avatar animé</span>
        <button
          onClick={toggleAvatar}
          className={`w-12 h-6 rounded-full transition-colors ${
            avatarEnabled ? 'bg-primary-500' : 'bg-gray-600'
          }`}
        >
          <div
            className={`w-5 h-5 bg-white rounded-full transition-transform ${
              avatarEnabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      <div className="flex items-center justify-between">
        <span>Mode HD (Duix)</span>
        <select className="input text-sm" defaultValue="realtime">
          <option value="realtime">Temps réel</option>
          <option value="hd">Haute qualité</option>
        </select>
      </div>
    </div>
  );
}