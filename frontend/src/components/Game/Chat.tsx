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
      handleSend("Peux-tu m'expliquer le concept et à quoi sert cette configuration ?");
    } else if (type === 'hint') {
      handleSend("Je suis bloqué, donne-moi un indice s'il te plaît.");
    } else if (type === 'check') {
      handleSend("Peux-tu vérifier ce que j'ai fait pour voir si c'est correct ?");
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#090D1A]/50 relative select-none">
      
      {/* Premium Chat header */}
      <div className="px-5 py-4.5 border-b border-gray-850 bg-[#090D1A] flex justify-between items-center shrink-0">
        <span className="font-mono text-xs text-gray-300 font-bold flex items-center space-x-2">
          <Sparkles className="h-4 w-4 text-[#10B981]" />
          <span>Coéquipier IA</span>
        </span>
        <div className="flex items-center space-x-1.5">
          <span className={`h-2 w-2 rounded-full ${connected ? 'bg-[#10B981] animate-pulse' : 'bg-red-500'}`}></span>
          <span className="text-[10px] text-gray-500 font-bold font-mono uppercase tracking-wider">{connected ? 'ONLINE' : 'OFFLINE'}</span>
        </div>
      </div>

      {/* Message history with Discord-like bubbles */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.map((msg, index) => {
          const isAI = msg.sender === 'ai';
          return (
            <div key={index} className={`flex ${isAI ? 'justify-start' : 'justify-end'}`}>
              <div className={`max-w-[90%] rounded-2xl p-3.5 text-xs leading-relaxed font-mono shadow-md ${
                isAI 
                  ? 'bg-[#040712] text-gray-300 border border-gray-850' 
                  : 'bg-[#10B981]/10 text-white border border-[#10B981]/25'
              }`}>
                <div className="flex items-center space-x-1.5 mb-1.5 text-[9px] font-bold uppercase tracking-wider text-gray-500">
                  {isAI ? <Cpu className="h-3 w-3 text-[#10B981]" /> : <User className="h-3 w-3 text-emerald-400" />}
                  <span>{isAI ? 'Coéquipier' : 'Vous'}</span>
                </div>
                <p className="whitespace-pre-wrap leading-relaxed select-text">{msg.message}</p>
              </div>
            </div>
          );
        })}

        {typing && (
          <div className="flex justify-start">
            <div className="bg-[#040712] border border-gray-850 rounded-2xl p-3.5 text-xs text-gray-400 font-mono shadow-md flex items-center space-x-2">
              <span className="h-1.5 w-1.5 bg-gray-500 rounded-full animate-bounce"></span>
              <span className="h-1.5 w-1.5 bg-gray-500 rounded-full animate-bounce [animation-delay:0.2s]"></span>
              <span className="h-1.5 w-1.5 bg-gray-500 rounded-full animate-bounce [animation-delay:0.4s]"></span>
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Suggested prompts list */}
      <div className="px-5 py-2.5 border-t border-gray-850/60 bg-gray-950/20 flex flex-wrap gap-1.5 shrink-0">
        <button
          onClick={() => handleSuggest('hint')}
          className="px-3 py-1.5 bg-[#040712] hover:bg-gray-900 text-[10px] font-bold font-mono text-gray-400 hover:text-white rounded-lg border border-gray-800 transition-all"
        >
          💡 Un indice ?
        </button>
        <button
          onClick={() => handleSuggest('concept')}
          className="px-3 py-1.5 bg-[#040712] hover:bg-gray-900 text-[10px] font-bold font-mono text-gray-400 hover:text-white rounded-lg border border-gray-800 transition-all"
        >
          📖 Explique le concept
        </button>
        <button
          onClick={() => handleSuggest('check')}
          className="px-3 py-1.5 bg-[#040712] hover:bg-gray-900 text-[10px] font-bold font-mono text-gray-400 hover:text-white rounded-lg border border-gray-800 transition-all"
        >
          🔍 Vérifie mon travail
        </button>
      </div>

      {/* Message input */}
      <div className="p-4 border-t border-gray-850 bg-[#090D1A] flex space-x-2 shrink-0">
        <input
          type="text"
          placeholder="Posez une question..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 bg-[#040712] border border-gray-800 focus:border-[#10B981]/50 focus:outline-none px-3 py-2 rounded-xl text-xs font-mono select-text"
        />
        <button
          onClick={() => handleSend()}
          className="p-2.5 bg-[#10B981]/15 hover:bg-[#10B981] border border-[#10B981]/25 hover:text-black rounded-xl text-[#10B981] transition-all"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
