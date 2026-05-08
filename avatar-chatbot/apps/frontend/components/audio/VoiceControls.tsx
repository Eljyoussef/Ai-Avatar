'use client';

import { useState } from 'react';
import { wsService } from '@/services/websocket.service';
import { useChatStore } from '@/stores/chatStore';

export function VoiceControls() {
  const [isRecording, setIsRecording] = useState(false);
  const { isSpeaking } = useChatStore();
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          event.data.arrayBuffer().then((buffer) => {
            wsService.sendAudio(buffer);
          });
        }
      };

      recorder.start(100); // Send chunks every 100ms
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (error) {
      console.error('Microphone access denied:', error);
      alert('Veuillez autoriser l\'accès au microphone');
    }
  };

  const stopRecording = () => {
    mediaRecorder?.stop();
    mediaRecorder?.stream.getTracks().forEach((track) => track.stop());
    setMediaRecorder(null);
    setIsRecording(false);
  };

  const handleInterrupt = () => {
    wsService.sendInterrupt();
  };

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4">🎤 Contrôle Vocal</h2>

      <div className="flex gap-4 justify-center">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl transition-all ${
            isRecording
              ? 'bg-red-500 voice-active scale-110'
              : 'bg-primary-500 hover:bg-primary-700'
          }`}
        >
          {isRecording ? '⏹' : '🎙️'}
        </button>

        {isSpeaking && (
          <button
            onClick={handleInterrupt}
            className="w-16 h-16 rounded-full bg-yellow-500 hover:bg-yellow-600 flex items-center justify-center text-2xl"
            title="Interrompre"
          >
            ⏸
          </button>
        )}
      </div>

      <div className="text-center mt-4">
        <p className="text-sm text-gray-400">
          {isRecording ? '🔴 Enregistrement...' : isSpeaking ? '🟢 En train de parler...' : 'Prêt à écouter'}
        </p>
      </div>
    </div>
  );
}