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
    const backendHost = window.location.port === '3000' ? 'localhost:8000' : window.location.host;
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
            // Avoid duplicate greetings on connection setup
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

  // Autoscroll to bottom
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  const handleSend = (textToSend?: string) => {
    const message = textToSend || inputText;
    if (!message.trim() || !wsRef.current) return;

    // Append to local message list
    setMessages(prev => [...prev, { sender: 'user', message }]);
    
    // Send over socket
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
    <div className="flex-1 flex flex-col min-h-0 bg-[#0B0F19]">
      {/* Chat header */}
      <div className="px-4 py-2 border-b border-gray-850 bg-gray-950 flex justify-between items-center shrink-0">
        <span className="font-mono text-xs text-gray-400 flex items-center space-x-1.5">
          <Sparkles className="h-3.5 w-3.5 text-[#10B981]" />
          <span>Coéquipier IA</span>
        </span>
        <span className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-[#10B981]' : 'bg-red-500'}`}></span>
      </div>

      {/* Message history */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => {
          const isAI = msg.sender === 'ai';
          return (
            <div key={index} className={`flex ${isAI ? 'justify-start' : 'justify-end'}`}>
              <div className={`max-w-[85%] rounded-xl p-3 text-xs leading-relaxed font-mono ${
                isAI 
                  ? 'bg-gray-900 text-gray-200 border border-gray-800' 
                  : 'bg-[#10B981]/10 text-white border border-[#10B981]/20'
              }`}>
                <div className="flex items-center space-x-1.5 mb-1 text-[10px] text-gray-500">
                  {isAI ? <Cpu className="h-3 w-3 text-[#10B981]" /> : <User className="h-3 w-3 text-emerald-400" />}
                  <span>{isAI ? 'Coéquipier' : 'Vous'}</span>
                </div>
                <p className="whitespace-pre-wrap">{msg.message}</p>
              </div>
            </div>
          );
        })}

        {typing && (
          <div className="flex justify-start">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-3 text-xs text-gray-400 font-mono">
              <span className="animate-pulse">Mon coéquipier réfléchit...</span>
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Suggested prompts list */}
      <div className="px-4 py-2 border-t border-gray-850 bg-gray-950/40 flex flex-wrap gap-1.5 shrink-0">
        <button
          onClick={() => handleSuggest('hint')}
          className="px-2 py-1 bg-gray-900 hover:bg-gray-850 text-[10px] font-mono text-gray-400 hover:text-white rounded border border-gray-800 transition"
        >
          💡 Un indice ?
        </button>
        <button
          onClick={() => handleSuggest('concept')}
          className="px-2 py-1 bg-gray-900 hover:bg-gray-850 text-[10px] font-mono text-gray-400 hover:text-white rounded border border-gray-800 transition"
        >
          📖 Explique le concept
        </button>
        <button
          onClick={() => handleSuggest('check')}
          className="px-2 py-1 bg-gray-900 hover:bg-gray-850 text-[10px] font-mono text-gray-400 hover:text-white rounded border border-gray-800 transition"
        >
          🔍 Vérifie mon travail
        </button>
      </div>

      {/* Message input */}
      <div className="p-3 border-t border-gray-850 bg-gray-950 flex space-x-2 shrink-0">
        <input
          type="text"
          placeholder="Posez une question..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 bg-gray-900 border border-gray-800 focus:border-[#10B981]/50 focus:outline-none p-2 rounded-lg text-xs font-mono"
        />
        <button
          onClick={() => handleSend()}
          className="p-2 bg-[#10B981]/15 hover:bg-[#10B981] border border-[#10B981]/25 hover:text-black rounded-lg text-[#10B981] transition"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
