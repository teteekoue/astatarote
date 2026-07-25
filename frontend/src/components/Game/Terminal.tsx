import React, { useEffect, useRef, useState } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { Terminal as TermIcon, TerminalSquare } from 'lucide-react';

interface TerminalProps {
  gameId: number;
  levelIndex: number;
}

export default function Terminal({ gameId, levelIndex }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const termInstanceRef = useRef<XTerm | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const inputBufferRef = useRef<string>('');
  const [connected, setConnected] = useState(false);

  // Initialize Terminal & WebSockets
  useEffect(() => {
    if (!terminalRef.current) return;

    const term = new XTerm({
      cursorBlink: true,
      fontFamily: 'JetBrains Mono, Menlo, Monaco, Consolas, monospace',
      fontSize: 13,
      lineHeight: 1.3,
      theme: {
        background: '#040712', // Slightly deeper black matching dashboard
        foreground: '#D1D5DB',
        cursor: '#10B981',
        selectionBackground: 'rgba(16, 185, 129, 0.25)',
        black: '#1F2937',
        red: '#F87171',
        green: '#34D399',
        yellow: '#FBBF24',
        blue: '#60A5FA',
        magenta: '#A78BFA',
        cyan: '#22D3EE',
        white: '#F3F4F6'
      }
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(terminalRef.current);
    fitAddon.fit();
    termInstanceRef.current = term;

    // Setup WebSocket connection
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendHost = window.location.port === '3000' ? '127.0.0.1:8000' : window.location.host;
    const wsUrl = `${wsProtocol}//${backendHost}/ws/terminal/${gameId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      term.writeln("\r\n\x1b[32m[SYSTEM] Connexion établie avec la sandbox d'Astatarote.\x1b[0m\r\n");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.output) {
          term.write(data.output);
        }
      } catch (e) {
        term.write(event.data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      term.writeln("\r\n\x1b[31m[SYSTEM] Connexion interrompue.\x1b[0m");
    };

    ws.onerror = () => {
      term.writeln("\r\n\x1b[31m[SYSTEM] Erreur de connexion websocket.\x1b[0m");
    };

    term.onData((data) => {
      if (ws.readyState !== WebSocket.OPEN) return;

      for (let i = 0; i < data.length; i++) {
        const char = data[i];

        if (char === '\r') {
          const command = inputBufferRef.current;
          term.write('\r\n');
          ws.send(JSON.stringify({ command }));
          inputBufferRef.current = '';
        } else if (char === '\u007F') {
          if (inputBufferRef.current.length > 0) {
            inputBufferRef.current = inputBufferRef.current.slice(0, -1);
            term.write('\b \b');
          }
        } else {
          inputBufferRef.current += char;
          term.write(char);
        }
      }
    });

    const handleResize = () => {
      try {
        fitAddon.fit();
      } catch (err) {}
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      ws.close();
      term.dispose();
    };
  }, [gameId, levelIndex]);

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#040712] relative rounded-2xl border border-gray-800/80 shadow-2xl overflow-hidden m-4">
      
      {/* Premium Mac-style Terminal Header with Dots */}
      <div className="px-5 py-3.5 border-b border-gray-850 bg-[#090D1A] flex justify-between items-center shrink-0 select-none">
        
        {/* Left Mac dots */}
        <div className="flex items-center space-x-2">
          <div className="h-3 w-3 rounded-full bg-[#EF4444]/80 border border-red-600/20"></div>
          <div className="h-3 w-3 rounded-full bg-[#F59E0B]/80 border border-amber-600/20"></div>
          <div className="h-3 w-3 rounded-full bg-[#10B981]/80 border border-green-600/20"></div>
        </div>

        {/* Center TTY Window Title */}
        <span className="font-mono text-xs text-gray-400 font-bold flex items-center space-x-1.5 absolute left-1/2 transform -translate-x-1/2">
          <TerminalSquare className="h-3.5 w-3.5 text-[#10B981]" />
          <span>sh - tty_terminal_sandbox - index:{levelIndex + 1}</span>
        </span>

        {/* Right Status tag */}
        <div className="flex items-center space-x-2">
          <span className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-[#10B981] animate-pulse' : 'bg-red-500'}`}></span>
          <span className="text-[10px] text-gray-500 font-bold font-mono">ASTA_TTY</span>
        </div>
      </div>

      {/* Terminal Viewport */}
      <div className="flex-1 p-4 bg-[#040712] min-h-0">
        <div ref={terminalRef} className="h-full w-full" />
      </div>
    </div>
  );
}
