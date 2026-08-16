import React, { useEffect, useRef, useState } from "react";
import { Terminal as XTerm } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import "xterm/css/xterm.css";
import { TerminalSquare, Wifi, WifiOff } from "lucide-react";
import { wsUrl } from "../../lib/api";

interface TerminalProps {
  gameId: number;
  levelIndex: number;
  fontSize?: number;
}

export default function Terminal({ gameId, levelIndex, fontSize = 14 }: TerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<XTerm | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const fitRef = useRef<FitAddon | null>(null);
  const levelIndexRef = useRef(levelIndex);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    levelIndexRef.current = levelIndex;
  }, [levelIndex]);

  useEffect(() => {
    if (!containerRef.current) return;

    const term = new XTerm({
      cursorBlink: true,
      fontFamily: "JetBrains Mono, Menlo, Monaco, monospace",
      fontSize,
      lineHeight: 1.25,
      allowProposedApi: true,
      scrollback: 10000,
      theme: {
        background: "#04070f",
        foreground: "#d1d5db",
        cursor: "#10b981",
        cursorAccent: "#04070f",
        selectionBackground: "rgba(16, 185, 129, 0.3)",
        black: "#0f172a",
        red: "#f87171",
        green: "#34d399",
        yellow: "#fbbf24",
        blue: "#60a5fa",
        magenta: "#a78bfa",
        cyan: "#22d3ee",
        white: "#f8fafc",
        brightBlack: "#475569",
        brightRed: "#f87171",
        brightGreen: "#34d399",
        brightYellow: "#fbbf24",
        brightBlue: "#60a5fa",
        brightMagenta: "#a78bfa",
        brightCyan: "#22d3ee",
        brightWhite: "#ffffff",
      },
    });

    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(containerRef.current);
    fit.fit();
    termRef.current = term;
    fitRef.current = fit;
    term.focus();

    const connect = () => {
      const ws = new WebSocket(wsUrl(`/ws/terminal/${gameId}?level=${levelIndex}`));
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        // Report current size so the PTY matches the viewport
        const dims = termRef.current?.cols ?? 80;
        const rows = termRef.current?.rows ?? 24;
        ws.send(JSON.stringify({ type: "resize", cols: dims, rows }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (typeof data.output === "string") {
            termRef.current?.write(data.output);
          }
        } catch {
          termRef.current?.write(event.data);
        }
      };

      ws.onclose = () => {
        setConnected(false);
      };
      ws.onerror = () => {
        setConnected(false);
      };
    };

    connect();

    const handleResize = () => {
      try {
        fitRef.current?.fit();
        if (wsRef.current?.readyState === WebSocket.OPEN && termRef.current) {
          wsRef.current.send(
            JSON.stringify({
              type: "resize",
              cols: termRef.current.cols,
              rows: termRef.current.rows,
            })
          );
        }
      } catch {
        /* ignore */
      }
    };

    // Forward every keystroke / control sequence straight to the shell
    const dataDisposable = term.onData((data) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ command: data }));
      }
    });

    window.addEventListener("resize", handleResize);
    const fitObserver = new ResizeObserver(handleResize);
    if (containerRef.current) {
      fitObserver.observe(containerRef.current);
    }

    return () => {
      dataDisposable.dispose();
      window.removeEventListener("resize", handleResize);
      fitObserver.disconnect();
      wsRef.current?.close();
      term.dispose();
      termRef.current = null;
    };
  }, [gameId, levelIndex, fontSize]);

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#04070f] relative rounded-2xl border border-ink-line overflow-hidden m-4 shadow-card">
      {/* Terminal header */}
      <div className="px-5 py-3 border-b border-ink-line bg-ink-panel/90 flex justify-between items-center shrink-0 select-none">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <span className="h-3 w-3 rounded-full bg-red-500/80"></span>
            <span className="h-3 w-3 rounded-full bg-amber-500/80"></span>
            <span className="h-3 w-3 rounded-full bg-asta-green/80"></span>
          </div>
          <span className="ml-3 font-mono text-xs text-gray-400 font-bold flex items-center gap-2">
            <TerminalSquare className="h-3.5 w-3.5 text-asta-green" />
            sandbox bash — level {levelIndex + 1}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              connected ? "bg-asta-green animate-pulse-glow" : "bg-red-500"
            }`}
          ></span>
          {connected ? (
            <Wifi className="h-3 w-3 text-asta-green" />
          ) : (
            <WifiOff className="h-3 w-3 text-red-500" />
          )}
          <span className="text-[10px] font-mono text-gray-500 font-bold">ASTA_PTY</span>
        </div>
      </div>

      {/* Terminal viewport */}
      <div className="flex-1 min-h-0 p-3">
        <div ref={containerRef} className="h-full w-full" />
      </div>
    </div>
  );
}
