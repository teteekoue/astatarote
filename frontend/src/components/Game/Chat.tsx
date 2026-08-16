import React, { useState, useEffect, useRef } from "react";
import { Send, Bot, User, Sparkles, Lightbulb, SearchCheck, Wifi, WifiOff } from "lucide-react";
import { wsUrl } from "../../lib/api";

interface ChatProps {
  gameId: number;
}

interface MessageType {
  sender: string;
  message: string;
  timestamp?: string;
}

const SUGGESTIONS = [
  { key: "hint", label: "Un indice ?", icon: Lightbulb },
  { key: "concept", label: "Explique un concept", icon: Sparkles },
  { key: "check", label: "Vérifie mon travail", icon: SearchCheck },
];

export default function Chat({ gameId }: ChatProps) {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [inputText, setInputText] = useState("");
  const [connected, setConnected] = useState(false);
  const [typing, setTyping] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = new WebSocket(wsUrl(`/ws/chat/${gameId}`));
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.sender) {
          setMessages((prev) => {
            if (prev.some((m) => m.message === data.message && m.sender === data.sender)) return prev;
            return [...prev, data];
          });
          setTyping(false);
        }
      } catch {
        /* ignore */
      }
    };
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [gameId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const handleSend = (textToSend?: string) => {
    const message = (textToSend ?? inputText).trim();
    if (!message || !wsRef.current) return;

    setMessages((prev) => [...prev, { sender: "user", message }]);
    wsRef.current.send(JSON.stringify({ message }));
    if (!textToSend) setInputText("");
    setTyping(true);
  };

  const handleSuggestion = (key: string) => {
    if (key === "hint") handleSend("Je suis bloqué, donne-moi un indice progressif sans la solution.");
    if (key === "concept") handleSend("Explique-moi le concept clé de ce défi.");
    if (key === "check") handleSend("Vérifie ma démarche : je viens d'exécuter des commandes, dis-moi si je suis sur la bonne voie.");
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-ink-deep/60 relative select-none">
      {/* Header */}
      <div className="px-4 py-3 border-b border-ink-line bg-ink-panel/70 flex justify-between items-center shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-asta-green/10 border border-asta-green/30 flex items-center justify-center">
            <Bot className="h-4.5 w-4.5 text-asta-green" />
          </div>
          <div>
            <p className="font-mono text-xs font-black text-white tracking-wide">NEMESIS</p>
            <p className="text-[8px] text-asta-green font-mono tracking-widest uppercase font-bold">
              Coéquipier IA pédagogique
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className={`h-2 w-2 rounded-full ${
              connected ? "bg-asta-green animate-pulse-glow" : "bg-red-500"
            }`}
          ></span>
          {connected ? <Wifi className="h-3 w-3 text-asta-green" /> : <WifiOff className="h-3 w-3 text-red-500" />}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => {
          const isAI = msg.sender === "ai";
          return (
            <div key={index} className={`flex ${isAI ? "justify-start" : "justify-end"} animate-fade-in`}>
              <div
                className={`max-w-[90%] rounded-2xl p-3.5 text-xs leading-relaxed font-mono border shadow-sm ${
                  isAI
                    ? "bg-ink-panel/80 text-gray-300 border-ink-line/80"
                    : "bg-asta-green/10 text-gray-100 border-asta-green/20"
                }`}
              >
                <div className="flex items-center gap-2 mb-2 text-[8px] font-black uppercase tracking-wider text-gray-500 border-b border-ink-line/40 pb-1.5">
                  {isAI ? (
                    <>
                      <Bot className="h-3 w-3 text-asta-green" />
                      <span className="text-asta-green font-black">NEMESIS</span>
                    </>
                  ) : (
                    <>
                      <User className="h-3 w-3 text-gray-400" />
                      <span>Vous</span>
                    </>
                  )}
                </div>
                <p className="whitespace-pre-wrap break-words leading-relaxed select-text text-[11px]">{msg.message}</p>
              </div>
            </div>
          );
        })}

        {typing && (
          <div className="flex justify-start">
            <div className="bg-ink-panel/80 border border-ink-line/80 rounded-2xl p-4 text-xs text-gray-400 font-mono shadow-sm flex items-center gap-2">
              <span className="text-gray-500 text-[10px] uppercase font-bold tracking-widest">Nemesis écrit</span>
              <div className="flex gap-1">
                <span className="h-1.5 w-1.5 bg-asta-green rounded-full animate-bounce"></span>
                <span className="h-1.5 w-1.5 bg-asta-green rounded-full animate-bounce [animation-delay:0.15s]"></span>
                <span className="h-1.5 w-1.5 bg-asta-green rounded-full animate-bounce [animation-delay:0.3s]"></span>
              </div>
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Suggestions */}
      <div className="px-3 py-2 border-t border-ink-line/50 bg-ink-panel/40 flex flex-wrap gap-1.5 shrink-0">
        {SUGGESTIONS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => handleSuggestion(key)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-ink-deep/60 hover:bg-asta-green/10 text-[10px] font-bold font-mono text-gray-400 hover:text-white rounded-lg border border-ink-line hover:border-asta-green/40 transition-all duration-200"
          >
            <Icon className="h-3 w-3 text-asta-green" />
            {label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-ink-line/60 bg-ink-panel/70 flex gap-2 shrink-0">
        <input
          type="text"
          placeholder="Pose ta question à Nemesis..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          className="flex-1 bg-ink-deep/70 border border-ink-line rounded-xl px-3.5 py-2.5 text-xs font-mono select-text outline-none focus:border-asta-green/50 transition"
        />
        <button
          onClick={() => handleSend()}
          className="p-2.5 bg-asta-green/10 hover:bg-asta-green hover:text-black border border-asta-green/25 rounded-xl text-asta-green transition-all duration-300"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
