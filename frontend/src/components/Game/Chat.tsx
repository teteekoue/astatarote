import React, { useEffect, useRef, useState } from "react";
import { Bot, SendHorizonal, Sparkles, Loader2 } from "lucide-react";
import { wsUrl } from "../../lib/api";
import Markdown from "../Markdown";

interface ChatProps {
  gameId: number;
  levelIndex: number;
}

interface ChatMessage {
  sender: "user" | "ai";
  message: string;
  timestamp: string;
}

export default function Chat({ gameId, levelIndex }: ChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [connected, setConnected] = useState(false);
  const [thinking, setThinking] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    setMessages([]);
    let manuallyClosed = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      const ws = new WebSocket(wsUrl(`/ws/chat/${gameId}?level=${levelIndex}`));
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.sender === "user") return; // our own messages are already displayed
          setMessages((prev) => [...prev, msg as ChatMessage]);
        } catch {
          /* ignore */
        } finally {
          setThinking(false);
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!manuallyClosed) reconnectTimer = setTimeout(connect, 2000);
      };
    };
    connect();

    return () => {
      manuallyClosed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [gameId, levelIndex]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, thinking]);

  const send = (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || !connected) return;
    setMessages((prev) => [
      ...prev,
      { sender: "user", message: text, timestamp: new Date().toISOString() },
    ]);
    wsRef.current?.send(JSON.stringify({ message: text }));
    setInput("");
    setThinking(true);
  };

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-card">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-border px-4 py-3">
        <div className="relative flex h-8 w-8 items-center justify-center rounded-xl border border-primary/30 bg-primary/10">
          <Bot className="h-4 w-4 text-primary" />
          {connected && (
            <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-surface bg-accent" />
          )}
        </div>
        <div className="min-w-0 flex-1 leading-tight">
          <p className="text-[13px] font-semibold">Nemesis</p>
          <p className="truncate text-[11px] text-muted">
            {connected ? "assistante pédagogique · en ligne" : "reconnexion…"}
          </p>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
        {messages.map((msg, i) =>
          msg.sender === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[85%] rounded-2xl rounded-br-md bg-primary px-3.5 py-2.5 text-sm leading-relaxed text-white">
                {msg.message}
              </div>
            </div>
          ) : (
            <div key={i} className="flex justify-start">
              <div className="max-w-[92%] rounded-2xl rounded-bl-md border border-border bg-surface-2/60 px-3.5 py-2.5">
                <Markdown text={msg.message} />
              </div>
            </div>
          )
        )}
        {thinking && (
          <div className="flex items-center gap-2 px-2 text-muted">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span className="text-[12px]">Nemesis réfléchit…</span>
          </div>
        )}
      </div>

      {/* Composer */}
      <form onSubmit={send} className="border-t border-border p-3">
        <div className="flex items-end gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Posez votre question à Nemesis…"
            className="input py-2 text-[13px]"
            aria-label="Message à l'assistante Nemesis"
            maxLength={500}
          />
          <button
            type="submit"
            disabled={!input.trim() || !connected}
            className="btn-primary h-[38px] w-[42px] shrink-0 !p-0"
            aria-label="Envoyer"
          >
            <SendHorizonal className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-2 flex items-center gap-1.5 px-1 text-[11px] text-muted">
          <Sparkles className="h-3 w-3 text-primary" />
          Elle explique et oriente, mais ne donne jamais la solution brute.
        </p>
      </form>
    </div>
  );
}
