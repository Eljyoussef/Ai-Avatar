'use client';

import { useChatStore } from '@/stores/chatStore';
import { ACCENTS, VOICE_GENDERS } from '@/lib/constants';
import { wsService } from '@/services/websocket.service';

export function AccentSelector() {
  const { selectedAccent, setSelectedAccent, gender, setGender } = useChatStore();

  const handleAccentChange = (accent: string) => {
    setSelectedAccent(accent);
    wsService.sendCommand('accent_change', { accent });
  };

  const handleGenderChange = (newGender: string) => {
    setGender(newGender as 'male' | 'female' | 'neutral');
    wsService.sendCommand('gender_change', { gender: newGender });
  };

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4">🌍 Accent & Voix</h2>

      <div className="space-y-4">
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Accent régional</label>
          <select
            value={selectedAccent}
            onChange={(e) => handleAccentChange(e.target.value)}
            className="input w-full"
          >
            {ACCENTS.map((accent) => (
              <option key={accent.code} value={accent.code}>
                {accent.flag} {accent.name} ({accent.region})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm text-gray-400 mb-2 block">Genre de la voix</label>
          <div className="flex gap-2">
            {VOICE_GENDERS.map((g) => (
              <button
                key={g.value}
                onClick={() => handleGenderChange(g.value)}
                className={`flex-1 py-2 px-3 rounded-lg text-sm transition-colors ${
                  gender === g.value
                    ? 'bg-primary-500 text-white'
                    : 'bg-dark-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {g.icon} {g.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}