import React, { useEffect, useRef, useState } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { Play, Sparkles } from 'lucide-react';

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

    // Create XTerm instance with styled theme
    const term = new XTerm({
      cursorBlink: true,
      fontFamily: 'JetBrains Mono, Courier New, monospace',
      fontSize: 13,
      lineHeight: 1.25,
      theme: {
        background: '#070A13',
        foreground: '#E5E7EB',
        cursor: '#10B981',
        selectionBackground: 'rgba(16, 185, 129, 0.3)',
        black: '#1F2937',
        red: '#EF4444',
        green: '#10B981',
        yellow: '#F59E0B',
        blue: '#3B82F6',
        magenta: '#8B5CF6',
        cyan: '#06B6D4',
        white: '#F9FAFB'
      }
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(terminalRef.current);
    fitAddon.fit();
    termInstanceRef.current = term;

    // Setup WebSocket connection
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendHost = window.location.port === '3000' ? 'localhost:8000' : window.location.host;
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

    // Keyboard inputs handling
    term.onData((data) => {
      if (ws.readyState !== WebSocket.OPEN) return;

      for (let i = 0; i < data.length; i++) {
        const char = data[i];

        if (char === '\r') { // Enter key
          const command = inputBufferRef.current;
          term.write('\r\n');
          
          // Send command over socket
          ws.send(JSON.stringify({ command }));
          inputBufferRef.current = '';
        } else if (char === '\u007F') { // Backspace key
          if (inputBufferRef.current.length > 0) {
            inputBufferRef.current = inputBufferRef.current.slice(0, -1);
            term.write('\b \b');
          }
        } else {
          // Standard letters/char
          inputBufferRef.current += char;
          term.write(char);
        }
      }
    });

    // Resize handler
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
    <div className="flex-1 flex flex-col min-h-0 relative">
      {/* Top Header */}
      <div className="px-4 py-2 border-b border-gray-850 bg-gray-950 flex justify-between items-center shrink-0">
        <span className="font-mono text-xs text-gray-400 flex items-center space-x-2">
          <span className={`inline-block h-2 w-2 rounded-full ${connected ? 'bg-[#10B981]' : 'bg-red-500 animate-pulse'}`}></span>
          <span>Terminal Sandbox ({connected ? 'En ligne' : 'Déconnecté'})</span>
        </span>
        <span className="text-[10px] text-gray-500 font-mono">ASTA_TTYv1.0</span>
      </div>

      {/* Terminal Viewport */}
      <div className="flex-1 p-3 bg-[#070A13] min-h-0">
        <div ref={terminalRef} className="h-full w-full" />
      </div>
    </div>
  );
}
