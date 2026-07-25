import React, { useState, useEffect, useRef } from 'react';
import { Send, User, Cpu, Sparkles } from 'lucide-react';

interface ChatProps {
  gameId: number;
}

interface MessageType {
  sender: string;
  message: string;
  timestamp?: string;
}

export default function Chat({ gameId }: ChatProps) {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [inputText, setInputText] = useState('');
  const [connected, setConnected] = useState(false);
  const [typing, setTyping] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Setup WebSocket connection
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendHost = window.location.port === '3000' ? '127.0.0.1:8000' : window.location.host;
    const wsUrl = `${wsProtocol}//${backendHost}/ws/chat/${gameId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.sender) {
          setMessages(prev => {
            if (prev.some(m => m.message === data.message)) return prev;
            return [...prev, data];
          });
          setTyping(false);
        }
      } catch (e) {
        console.error("Chat parse error", e);
      }
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [gameId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  const handleSend = (textToSend?: string) => {
    const message = textToSend || inputText;
    if (!message.trim() || !wsRef.current) return;

    setMessages(prev => [...prev, { sender: 'user', message }]);
    wsRef.current.send(JSON.stringify({ message }));
    
    if (!textToSend) {
      setInputText('');
    }
    setTyping(true);
  };

  const handleSuggest = (type: 'concept' | 'hint' | 'check') => {
    if (type === 'concept') {
      handleSend("Nemesis, peux-tu m'expliquer le concept et à quoi sert cette configuration ?");
    } else if (type === 'hint') {
      handleSend("Nemesis, je suis bloqué, donne-moi un indice s'il te plaît.");
    } else if (type === 'check') {
      handleSend("Nemesis, peux-tu vérifier mon travail pour voir si c'est correct ?");
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#050816]/90 relative select-none">
      
      {/* Modern ChatGPT-style Chat Header */}
      <div className="px-5 py-4.5 border-b border-gray-850 bg-[#060919] flex justify-between items-center shrink-0">
        <div className="flex items-center space-x-2.5">
          <div className="h-7 w-7 rounded-lg bg-[#10B981]/10 border border-[#10B981]/30 flex items-center justify-center">
            <Cpu className="h-4 w-4 text-[#10B981]" />
          </div>
          <div className="text-left">
            <p className="font-mono text-xs font-black text-white tracking-wide">NEMESIS</p>
            <p className="text-[8px] text-[#10B981] font-mono tracking-widest uppercase font-bold">COÉQUIPIER IA ADAPTATIF</p>
          </div>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className={`h-2 w-2 rounded-full ${connected ? 'bg-[#10B981] animate-pulse' : 'bg-red-500'}`}></span>
          <span className="text-[8px] text-gray-500 font-bold font-mono uppercase tracking-widest">{connected ? 'ONLINE' : 'OFFLINE'}</span>
        </div>
      </div>

      {/* Message history with distinct ChatGPT-style text blocks */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.map((msg, index) => {
          const isAI = msg.sender === 'ai';
          
          // Rename greeting message to introduce "Nemesis"
          let text = msg.message;
          if (isAI && text.includes("Je suis ton coéquipier d'apprentissage")) {
            text = text.replace("Je suis ton coéquipier d'apprentissage", "Je suis Nemesis, ton coéquipier d'apprentissage cyber");
          }

          return (
            <div key={index} className={`flex ${isAI ? 'justify-start' : 'justify-end'}`}>
              <div className={`max-w-[90%] rounded-2xl p-4 text-xs leading-relaxed font-mono shadow-md border ${
                isAI 
                  ? 'bg-gray-950/40 text-gray-300 border-gray-850/60' 
                  : 'bg-[#10B981]/5 text-white border-[#10B981]/15'
              }`}>
                <div className="flex items-center space-x-2 mb-2 text-[9px] font-black uppercase tracking-wider text-gray-500 border-b border-gray-850/40 pb-1.5">
                  {isAI ? (
                    <>
                      <Cpu className="h-3 w-3 text-[#10B981]" />
                      <span className="text-[#10B981] font-black">NEMESIS</span>
                    </>
                  ) : (
                    <>
                      <User className="h-3 w-3 text-emerald-400" />
                      <span>Vous</span>
                    </>
                  )}
                </div>
                <p className="whitespace-pre-wrap leading-relaxed select-text">{text}</p>
              </div>
            </div>
          );
        })}

        {typing && (
          <div className="flex justify-start">
            <div className="bg-gray-950/40 border border-gray-850/60 rounded-2xl p-4 text-xs text-gray-400 font-mono shadow-md flex items-center space-x-2">
              <span className="text-gray-500 text-[10px] uppercase font-bold tracking-widest">Nemesis écrit</span>
              <div className="flex space-x-1">
                <span className="h-1 w-1 bg-[#10B981] rounded-full animate-bounce"></span>
                <span className="h-1 w-1 bg-[#10B981] rounded-full animate-bounce [animation-delay:0.2s]"></span>
                <span className="h-1 w-1 bg-[#10B981] rounded-full animate-bounce [animation-delay:0.4s]"></span>
              </div>
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Suggested prompts list */}
      <div className="px-5 py-2.5 border-t border-gray-850/50 bg-gray-950/20 flex flex-wrap gap-1.5 shrink-0">
        <button
          onClick={() => handleSuggest('hint')}
          className="px-3 py-1.5 bg-[#03050f]/80 hover:bg-[#10B981]/10 text-[10px] font-bold font-mono text-gray-400 hover:text-white rounded-lg border border-gray-850 transition-all duration-250"
        >
          💡 Un indice ?
        </button>
        <button
          onClick={() => handleSuggest('concept')}
          className="px-3 py-1.5 bg-[#03050f]/80 hover:bg-[#10B981]/10 text-[10px] font-bold font-mono text-gray-400 hover:text-white rounded-lg border border-gray-850 transition-all duration-250"
        >
          📖 Explique le concept
        </button>
        <button
          onClick={() => handleSuggest('check')}
          className="px-3 py-1.5 bg-[#03050f]/80 hover:bg-[#10B981]/10 text-[10px] font-bold font-mono text-gray-400 hover:text-white rounded-lg border border-gray-850 transition-all duration-250"
        >
          🔍 Vérifie mon travail
        </button>
      </div>

      {/* Message input */}
      <div className="p-4 border-t border-gray-850/60 bg-[#060919] flex space-x-2 shrink-0">
        <input
          type="text"
          placeholder="Écrivez votre question à Nemesis..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 bg-[#02040e] border border-gray-850 focus:border-[#10B981]/50 focus:outline-none px-4 py-2.5 rounded-xl text-xs font-mono select-text"
        />
        <button
          onClick={() => handleSend()}
          className="p-3 bg-[#10B981]/10 hover:bg-[#10B981] border border-[#10B981]/25 hover:text-black rounded-xl text-[#10B981] transition-all duration-300 shadow-md"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
