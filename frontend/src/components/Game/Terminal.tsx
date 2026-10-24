import React, { useEffect, useRef, useState } from "react";
import { Terminal as XTerm } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import "xterm/css/xterm.css";
import { CircleDot, Loader2 } from "lucide-react";
import { wsUrl } from "../../lib/api";

interface TerminalProps {
  gameId: number;
  levelIndex: number;
  fontSize?: number;
}

/**
 * Line-based terminal connected to the deterministic Linux engine.
 *
 * Unlike the old PTY mode, the server executes complete command lines and
 * returns the output; this component handles local line editing (echo,
 * backspace, history, tab-completion, Ctrl+C) on top of xterm.js.
 */
export default function Terminal({ gameId, levelIndex, fontSize = 14 }: TerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<XTerm | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const fitRef = useRef<FitAddon | null>(null);

  // Line-editor state (kept in refs: the xterm key handler is attached once).
  const bufferRef = useRef("");
  const promptRef = useRef("");
  const cursorRef = useRef(0);
  const historyRef = useRef<string[]>([]);
  const histIdxRef = useRef(-1);
  const busyRef = useRef(false); // waiting for server output

  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;

    const term = new XTerm({
      cursorBlink: true,
      fontFamily: "JetBrains Mono, Menlo, Monaco, monospace",
      fontSize,
      lineHeight: 1.3,
      allowProposedApi: true,
      scrollback: 5000,
      theme: {
        background: "#0A0F1E",
        foreground: "#D7DEEE",
        cursor: "#10B981",
        cursorAccent: "#0A0F1E",
        selectionBackground: "rgba(99, 102, 241, 0.35)",
        black: "#0A0F1E",
        red: "#EF4444",
        green: "#10B981",
        yellow: "#F59E0B",
        blue: "#818CF8",
        magenta: "#C084FC",
        cyan: "#22D3EE",
        white: "#E6EAF4",
        brightBlack: "#5A6486",
        brightRed: "#F87171",
        brightGreen: "#34D399",
        brightYellow: "#FBBF24",
        brightBlue: "#A5B4FC",
        brightMagenta: "#D8B4FE",
        brightCyan: "#67E8F9",
        brightWhite: "#FFFFFF",
      },
    });

    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(containerRef.current);
    fit.fit();
    termRef.current = term;
    fitRef.current = fit;
    term.focus();

    const redraft = () => {
      // Re-render the current prompt line (after edits / history moves).
      term.write("\r\x1b[K" + promptRef.current + bufferRef.current);
      // park the cursor at the end (simple editor without mid-line moves)
    };

    const setPrompt = (p: string) => {
      promptRef.current = p;
    };

    /* ------------------------- WebSocket handling ------------------------- */
    let manuallyClosed = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      const ws = new WebSocket(wsUrl(`/ws/terminal/${gameId}?level=${levelIndex}`));
      wsRef.current = ws;
      busyRef.current = true;

      ws.onopen = () => setConnected(true);

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "banner" || msg.type === "output") {
            if (msg.type === "output" && msg.output === promptRef.current) {
              // Server echo of the current prompt — just redraw the line.
              redraft();
              busyRef.current = false;
              return;
            }
            // Track the latest prompt (server always ends with it).
            const lines = String(msg.output ?? "").split("\n");
            const lastNonEmpty = lines[lines.length - 1] === "" ? lines[lines.length - 2] : lines[lines.length - 1];
            if (lastNonEmpty && /[#$] $/.test(lastNonEmpty)) {
              setPrompt(lastNonEmpty);
            }
            term.write(msg.output ?? "");
            busyRef.current = false;
          } else if (msg.type === "action" && msg.action === "clear") {
            term.clear();
            term.write(promptRef.current);
            busyRef.current = false;
          } else if (msg.type === "completion") {
            const candidates: string[] = msg.candidates ?? [];
            if (candidates.length === 1) {
              completeWith(candidates[0]);
            } else if (candidates.length > 1) {
              // Common prefix completion, like bash
              let prefix = candidates[0];
              for (const c of candidates.slice(1)) {
                while (!c.startsWith(prefix)) prefix = prefix.slice(0, -1);
              }
              if (prefix.length > 0) {
                completeWith(prefix);
              } else {
                term.write("\r\n" + candidates.join("   ") + "\r\n");
                redraft();
              }
            }
            busyRef.current = false;
          } else if (msg.type === "error") {
            term.write("\r\n\x1b[31m" + (msg.message ?? "erreur") + "\x1b[0m\r\n");
            busyRef.current = false;
          }
        } catch {
          /* ignore malformed frames */
        }
      };

      ws.onclose = () => {
        setConnected(false);
        busyRef.current = false;
        if (!manuallyClosed) {
          reconnectTimer = setTimeout(connect, 1500);
        }
      };
    };

    const completeWith = (candidate: string) => {
      // Replace the last token of the buffer with the candidate.
      const parts = bufferRef.current.split(" ");
      const isCmd = parts.length === 1;
      parts[parts.length - 1] = isCmd ? candidate : candidate.replace(/\/$/, "");
      bufferRef.current = parts.join(" ");
      redraft();
    };

    connect();

    /* --------------------------- Keyboard input --------------------------- */
    const dataHandler = term.onData((data) => {
      if (busyRef.current) return;

      if (data === "\r") {
        const line = bufferRef.current;
        term.write("\r\n");
        if (line.trim()) {
          historyRef.current.push(line);
        }
        histIdxRef.current = -1;
        bufferRef.current = "";
        if (line.trim()) {
          busyRef.current = true;
          wsRef.current?.send(JSON.stringify({ type: "input", line }));
        } else {
          term.write(promptRef.current);
        }
        return;
      }

      if (data === "\x7f") {
        if (bufferRef.current.length > 0) {
          bufferRef.current = bufferRef.current.slice(0, -1);
          redraft();
        }
        return;
      }

      if (data === "\x03") {
        term.write("^C\r\n" + promptRef.current);
        bufferRef.current = "";
        return;
      }

      if (data === "\t") {
        if (bufferRef.current.trim()) {
          busyRef.current = true;
          wsRef.current?.send(JSON.stringify({ type: "complete", line: bufferRef.current }));
        }
        return;
      }

      if (data === "\x1b[A") {
        // history up
        const h = historyRef.current;
        if (h.length === 0) return;
        if (histIdxRef.current === -1) histIdxRef.current = h.length - 1;
        else histIdxRef.current = Math.max(0, histIdxRef.current - 1);
        bufferRef.current = h[histIdxRef.current];
        redraft();
        return;
      }
      if (data === "\x1b[B") {
        // history down
        const h = historyRef.current;
        if (histIdxRef.current === -1) return;
        histIdxRef.current += 1;
        if (histIdxRef.current >= h.length) {
          histIdxRef.current = -1;
          bufferRef.current = "";
        } else {
          bufferRef.current = h[histIdxRef.current];
        }
        redraft();
        return;
      }

      // ignore other control sequences
      if (data >= " " || data === " ") {
        bufferRef.current += data;
        term.write(data);
      }
    });

    const resizeObserver = new ResizeObserver(() => {
      try {
        fitRef.current?.fit();
      } catch {
        /* ignore */
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      manuallyClosed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      resizeObserver.disconnect();
      dataHandler.dispose();
      wsRef.current?.close();
      term.dispose();
    };
    // Reconnect when the level changes.
  }, [gameId, levelIndex, fontSize]);

  return (
    <div className="relative flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-border bg-[#0A0F1E] shadow-card">
      <div className="flex items-center justify-between border-b border-border bg-surface px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-danger/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-warning/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-accent/70" />
          <span className="ml-2 font-mono text-[11px] text-muted">
            astarote@lab — moteur déterministe
          </span>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-[11px]">
          {connected ? (
            <>
              <CircleDot className="h-3.5 w-3.5 text-accent" />
              <span className="text-accent">connecté</span>
            </>
          ) : (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin text-muted" />
              <span className="text-muted">connexion…</span>
            </>
          )}
        </div>
      </div>
      <div
        ref={containerRef}
        className="terminal-shell min-h-0 flex-1 px-3 py-2"
        onClick={() => termRef.current?.focus()}
        role="application"
        aria-label="Terminal Linux simulé"
      />
    </div>
  );
}
