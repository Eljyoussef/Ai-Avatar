'use client';

import { useEffect, useRef, useState } from 'react';
import { wsService } from '@/services/websocket.service';
import { useChatStore } from '@/stores/chatStore';

interface Viseme {
  timestamp: number;
  openness: number;
  phoneme: string;
}

export function AvatarDisplay() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { isSpeaking, avatarEnabled } = useChatStore();
  const [visemes, setVisemes] = useState<Viseme[]>([]);
  const animationRef = useRef<number>(0);

  useEffect(() => {
    wsService.on('avatar.visemes', (data: any) => {
      setVisemes(data.visemes || []);
    });
  }, []);

  // Simple canvas-based avatar rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const drawAvatar = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Background circle
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      const radius = 100;

      // Face
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fillStyle = '#3b82f6';
      ctx.fill();
      ctx.strokeStyle = '#1d4ed8';
      ctx.lineWidth = 3;
      ctx.stroke();

      // Eyes
      const eyeY = cy - 20;
      ctx.fillStyle = 'white';
      ctx.beginPath();
      ctx.ellipse(cx - 35, eyeY, 15, 18, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.ellipse(cx + 35, eyeY, 15, 18, 0, 0, Math.PI * 2);
      ctx.fill();

      // Pupils
      ctx.fillStyle = '#1e3a5f';
      ctx.beginPath();
      ctx.arc(cx - 35, eyeY, 7, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx + 35, eyeY, 7, 0, Math.PI * 2);
      ctx.fill();

      // Mouth (animated based on speech)
      const currentViseme = visemes.length > 0 ? visemes[Math.floor(Date.now() / 16) % visemes.length] : null;
      const mouthOpenness = isSpeaking ? (currentViseme?.openness || 0.3) : 0.1;

      const mouthY = cy + 40;
      const mouthHeight = 5 + mouthOpenness * 30;

      ctx.fillStyle = '#1e3a5f';
      ctx.beginPath();
      ctx.ellipse(cx, mouthY, 25, mouthHeight, 0, 0, Math.PI * 2);
      ctx.fill();
    };

    const animate = () => {
      drawAvatar();
      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationRef.current);
    };
  }, [isSpeaking, visemes]);

  if (!avatarEnabled) {
    return (
      <div className="card flex items-center justify-center h-[300px]">
        <p className="text-gray-500">Avatar désactivé</p>
      </div>
    );
  }

  return (
    <div className="card">
      <canvas
        ref={canvasRef}
        width={300}
        height={300}
        className="mx-auto"
      />
      {isSpeaking && (
        <p className="text-center text-primary-500 text-sm mt-2 animate-pulse">
          🗣️ En train de parler...
        </p>
      )}
    </div>
  );
}