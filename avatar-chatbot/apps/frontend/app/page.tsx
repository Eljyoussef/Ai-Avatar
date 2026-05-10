'use client';

import { useState, useEffect, useRef } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isCallActive, setIsCallActive] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [selectedAccent, setSelectedAccent] = useState('fr-FR');
  const [gender, setGender] = useState<'male'|'female'|'neutral'>('neutral');
  const [avatarEnabled, setAvatarEnabled] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animRef = useRef<number>(0);

  const accents = [
    { code: 'fr-FR', name: 'Français standard', flag: '🇫🇷' },
    { code: 'fr-CA', name: 'Français québécois', flag: '🇨🇦' },
    { code: 'fr-AF', name: 'Français africain', flag: '🌍' },
    { code: 'fr-BE', name: 'Français belge', flag: '🇧🇪' },
    { code: 'fr-CH', name: 'Français suisse', flag: '🇨🇭' },
  ];

  useEffect(() => {
    const sid = crypto.randomUUID();
    setSessionId(sid);
    const ws = new WebSocket(`ws://localhost:8000/ws/${sid}`);
    wsRef.current = ws;
    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'text_response' && data.text) {
          setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: data.text, timestamp: Date.now() }]);
        }
        if (data.type === 'audio_chunk' && data.audio) {
          const bytes = new Uint8Array(data.audio.match(/.{1,2}/g).map((b: string) => parseInt(b, 16)));
          const blob = new Blob([bytes], { type: 'audio/wav' });
          const url = URL.createObjectURL(blob);
          if (audioRef.current) { audioRef.current.src = url; audioRef.current.play(); }
        }
      } catch {}
    };
    ws.onclose = () => setIsConnected(false);
    return () => ws.close();
  }, []);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // Canvas avatar animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !avatarEnabled) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const draw = () => {
      ctx.clearRect(0, 0, 200, 200);
      const cx = 100, cy = 100;
      ctx.beginPath(); ctx.arc(cx, cy, 80, 0, Math.PI*2); ctx.fillStyle = '#3b82f6'; ctx.fill();
      ctx.fillStyle = 'white';
      ctx.beginPath(); ctx.ellipse(cx-25, cy-15, 10, 14, 0, 0, Math.PI*2); ctx.fill();
      ctx.beginPath(); ctx.ellipse(cx+25, cy-15, 10, 14, 0, 0, Math.PI*2); ctx.fill();
      ctx.fillStyle = '#1e3a5f';
      ctx.beginPath(); ctx.arc(cx-25, cy-15, 5, 0, Math.PI*2); ctx.fill();
      ctx.beginPath(); ctx.arc(cx+25, cy-15, 5, 0, Math.PI*2); ctx.fill();
      ctx.beginPath(); ctx.ellipse(cx, cy+30, 18, 4+Math.sin(Date.now()/200)*3, 0, 0, Math.PI*2); ctx.fill();
      animRef.current = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [avatarEnabled]);

  const sendMessage = () => {
    if (!input.trim() || !wsRef.current) return;
    setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'user', content: input, timestamp: Date.now() }]);
    wsRef.current.send(JSON.stringify({ type: 'chat', content: input, accent: selectedAccent, gender }));
    setInput('');
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => { if (e.data.size > 0 && wsRef.current) e.data.arrayBuffer().then(b => wsRef.current!.send(b)); };
      recorder.start(250);
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch { alert('Microphone refusé'); }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current?.stream.getTracks().forEach(t => t.stop());
    setIsRecording(false);
    setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'user', content: '🎤 Message vocal', timestamp: Date.now() }]);
  };

  const toggleCall = async () => {
    if (isCallActive) { mediaRecorderRef.current?.stop(); setIsCallActive(false); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => { if (e.data.size > 0 && wsRef.current) e.data.arrayBuffer().then(b => wsRef.current!.send(b)); };
      recorder.start(100);
      mediaRecorderRef.current = recorder;
      setIsCallActive(true);
    } catch { alert('Microphone refusé'); }
  };

  const uploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData(); fd.append('file', file);
    try {
      await fetch('http://localhost:8000/api/upload', { method: 'POST', body: fd });
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'system', content: `📎 ${file.name} uploadé`, timestamp: Date.now() }]);
    } catch { alert('Upload échoué'); }
  };

  return (
    <main style={{ maxWidth:900, margin:'0 auto', padding:16, fontFamily:'system-ui', background:'#0a0a14', minHeight:'100vh', color:'#fff' }}>
      <audio ref={audioRef} style={{display:'none'}} />
      
      {/* Header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16, flexWrap:'wrap', gap:8 }}>
        <div>
          <h1 style={{ fontSize:24, margin:0, background:'linear-gradient(90deg,#3b82f6,#60a5fa)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' }}>🎙️ Avatar Chatbot</h1>
          <p style={{ color:'#888', fontSize:12, margin:0 }}>{isConnected ? '🟢 Connecté' : '🔴 Déconnecté'} | {sessionId.slice(0,8)}...</p>
        </div>
        <div style={{ display:'flex', gap:8, alignItems:'center', flexWrap:'wrap' }}>
          <select value={selectedAccent} onChange={e => setSelectedAccent(e.target.value)} style={{ padding:'6px 10px', borderRadius:8, background:'#1e1e2e', color:'#fff', border:'1px solid #4b5563', fontSize:12 }}>
            {accents.map(a => <option key={a.code} value={a.code}>{a.flag} {a.name}</option>)}
          </select>
          <select value={gender} onChange={e => setGender(e.target.value as any)} style={{ padding:'6px 10px', borderRadius:8, background:'#1e1e2e', color:'#fff', border:'1px solid #4b5563', fontSize:12 }}>
            <option value="female">👩 Féminin</option>
            <option value="male">👨 Masculin</option>
            <option value="neutral">🧑 Neutre</option>
          </select>
          <button onClick={() => setAvatarEnabled(!avatarEnabled)} style={{ padding:'6px 12px', borderRadius:8, background:avatarEnabled?'#22c55e':'#374151', color:'#fff', border:'none', fontSize:12, cursor:'pointer' }}>
            {avatarEnabled ? '👤 ON' : '👤 OFF'}
          </button>
        </div>
      </div>

      <div style={{ display:'flex', gap:16, flexWrap:'wrap' }}>
        {/* Avatar Panel */}
        {avatarEnabled && (
          <div style={{ background:'#1e1e2e', borderRadius:12, padding:16, textAlign:'center' }}>
            <canvas ref={canvasRef} width={200} height={200} />
            <p style={{ color:'#3b82f6', fontSize:12, marginTop:8 }}>🗣️ Avatar</p>
          </div>
        )}

        {/* Chat Area */}
        <div style={{ flex:1, minWidth:300 }}>
          <div style={{ height:400, overflowY:'auto', background:'#1e1e2e', borderRadius:12, padding:16, marginBottom:12 }}>
            {messages.length === 0 && <div style={{ textAlign:'center', color:'#666', marginTop:150 }}><p style={{fontSize:48}}>🎙️</p><p>Parlez ou écrivez</p></div>}
            {messages.map(msg => (
              <div key={msg.id} style={{ textAlign: msg.role==='user'?'right':msg.role==='system'?'center':'left', margin:'8px 0' }}>
                <span style={{ display:'inline-block', padding:'8px 14px', borderRadius:16, background: msg.role==='user'?'#3b82f6':msg.role==='system'?'#065f46':'#374151', maxWidth:'80%', fontSize:14 }}>
                  {msg.role!=='system' && <strong>{msg.role==='user'?'Vous':'Assistant'}:</strong>} {msg.content}
                </span>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Controls */}
          <div style={{ display:'flex', gap:8, alignItems:'center', flexWrap:'wrap' }}>
            <button onClick={toggleCall} title="Appel audio" style={{ width:44, height:44, borderRadius:'50%', border:'none', background: isCallActive?'#22c55e':'#3b82f6', color:'#fff', fontSize:18, cursor:'pointer', animation: isCallActive?'pulse 1.5s infinite':'none' }}>📞</button>
            <button onClick={isRecording?stopRecording:startRecording} title="Message vocal" style={{ width:44, height:44, borderRadius:'50%', border:'none', background: isRecording?'#ef4444':'#3b82f6', color:'#fff', fontSize:18, cursor:'pointer', animation: isRecording?'pulse 1.5s infinite':'none' }}>{isRecording?'⏹':'🎤'}</button>
            <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key==='Enter'&&sendMessage()} placeholder="Message..." disabled={!isConnected} style={{ flex:1, minWidth:150, padding:'10px 14px', borderRadius:12, border:'1px solid #4b5563', background:'#1e1e2e', color:'#fff', fontSize:14, outline:'none' }} />
            <button onClick={sendMessage} disabled={!isConnected} style={{ width:44, height:44, borderRadius:'50%', border:'none', background:'#3b82f6', color:'#fff', fontSize:18, cursor:isConnected?'pointer':'not-allowed', opacity:isConnected?1:0.5 }}>➤</button>
            <input ref={fileInputRef} type="file" onChange={uploadFile} style={{display:'none'}} accept=".pdf,.docx,.txt,.md" />
            <button onClick={() => fileInputRef.current?.click()} title="Upload" style={{ width:44, height:44, borderRadius:'50%', border:'none', background:'#8b5cf6', color:'#fff', fontSize:18, cursor:'pointer' }}>📎</button>
          </div>
        </div>
      </div>
      <style>{'@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,0.4)}50%{box-shadow:0 0 0 15px rgba(34,197,94,0)}}'}</style>
    </main>
  );
}