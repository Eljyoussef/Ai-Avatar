import type { Metadata } from 'next';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: 'Avatar Chatbot - Assistant Vocal Français',
  description: 'Assistant vocal français multi-accents avec avatar animé et RAG documentaire',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="antialiased">{children}</body>
    </html>
  );
}