export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

export const ACCENTS = [
  { code: 'fr-FR', name: 'Français standard', flag: '🇫🇷', region: 'France' },
  { code: 'fr-CA', name: 'Français québécois', flag: '🇨🇦', region: 'Québec' },
  { code: 'fr-AF', name: 'Français africain', flag: '🌍', region: 'Afrique' },
  { code: 'fr-BE', name: 'Français belge', flag: '🇧🇪', region: 'Belgique' },
  { code: 'fr-CH', name: 'Français suisse', flag: '🇨🇭', region: 'Suisse' },
  { code: 'fr-MG', name: 'Français maghrébin', flag: '🌅', region: 'Maghreb' },
];

export const VOICE_GENDERS = [
  { value: 'female', label: 'Voix féminine', icon: '👩' },
  { value: 'male', label: 'Voix masculine', icon: '👨' },
  { value: 'neutral', label: 'Neutre', icon: '🧑' },
];