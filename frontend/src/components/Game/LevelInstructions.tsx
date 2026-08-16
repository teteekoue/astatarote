import React, { useState } from "react";
import {
  Swords,
  ListChecks,
  BookOpen,
  Lightbulb,
  Compass,
  Clock,
  Trophy,
  Gauge,
  Terminal,
} from "lucide-react";
import { LevelType } from "./GameInterface";

interface LevelInstructionsProps {
  level: LevelType;
}

export default function LevelInstructions({ level }: LevelInstructionsProps) {
  const [activeTab, setActiveTab] = useState<"mission" | "support">("mission");

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return s > 0 ? `${m}m ${s}s` : `${m}m`;
  };

  const checks = level.scenario?.expected_state?.files_checks ?? [];

  const renderMarkdown = (text?: string) => {
    if (!text) return null;
    const lines = text.split("\n");
    const nodes: React.ReactNode[] = [];
    let codeLang = "";
    let codeLines: string[] = [];
    let key = 0;

    const flushCode = () => {
      if (codeLines.length === 0) return;
      nodes.push(
        <pre
          key={key++}
          className="my-2.5 p-3 rounded-xl bg-ink-deep border border-ink-line overflow-x-auto text-[11px] font-mono text-asta-green leading-relaxed whitespace-pre"
        >
          {codeLines.join("\n")}
        </pre>
      );
      codeLines = [];
      codeLang = "";
    };

    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();
      const fence = trimmed.match(/^```(\w*)/);

      if (fence || (trimmed.startsWith("~~~") && trimmed.trim().length <= 3)) {
        if (codeLines.length > 0 || codeLang !== "") {
          flushCode();
          continue;
        }
        codeLang = fence ? fence[1] : "";
        continue;
      }

      if (codeLines.length > 0 || codeLang !== "") {
        codeLines.push(lines[i]);
        continue;
      }

      if (trimmed.startsWith("###")) {
        nodes.push(
          <p key={key++} className="font-bold text-asta-green mt-4 mb-1 text-xs uppercase tracking-wider">
            {trimmed.replace(/^###\s*/, "")}
          </p>
        );
        continue;
      }
      if (trimmed.startsWith("##")) {
        nodes.push(
          <p key={key++} className="font-bold text-white mt-3 mb-1 text-xs uppercase tracking-wider">
            {trimmed.replace(/^##\s*/, "")}
          </p>
        );
        continue;
      }
      const orderedMatch = trimmed.match(/^(\d+)[).]\s+(.*)$/);
      if (orderedMatch) {
        nodes.push(
          <div key={key++} className="flex items-start gap-2 text-gray-300 leading-relaxed">
            <span className="text-asta-green mt-0.5 font-mono font-bold shrink-0">{orderedMatch[1]}.</span>
            <span className="whitespace-pre-wrap break-words font-mono text-[11px]">
              {renderInline(orderedMatch[2])}
            </span>
          </div>
        );
        continue;
      }
      if (trimmed.startsWith("- ")) {
        nodes.push(
          <div key={key++} className="flex items-start gap-2 text-gray-300 leading-relaxed">
            <span className="text-asta-green mt-1 shrink-0">•</span>
            <span className="whitespace-pre-wrap break-words font-mono text-[11px]">{renderInline(trimmed.slice(2))}</span>
          </div>
        );
        continue;
      }
      if (trimmed.startsWith("**") && trimmed.endsWith("**")) {
        nodes.push(
          <p key={key++} className="font-bold text-asta-green text-xs mt-1">
            {trimmed.slice(2, -2)}
          </p>
        );
        continue;
      }
      if (trimmed === "") {
        nodes.push(<div key={key++} className="h-2" />);
        continue;
      }
      nodes.push(
        <p key={key++} className="text-gray-300 leading-relaxed whitespace-pre-wrap break-words text-[11px]">
          {renderInline(lines[i])}
        </p>
      );
    }
    flushCode();

    return nodes;
  };

  const renderInline = (text: string) => {
    const parts = text.split(/(`[^`]+`)/g);
    return parts.map((part, j) =>
      part.startsWith("`") && part.endsWith("`") ? (
        <code key={j} className="px-1.5 py-0.5 rounded bg-ink-deep border border-ink-line text-asta-green font-mono text-[11px] break-words">
          {part.slice(1, -1)}
        </code>
      ) : (
        <span key={j}>{part}</span>
      )
    );
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-ink-deep/60 select-none">
      {/* Tabs */}
      <div className="flex border-b border-ink-line bg-ink-panel/60 p-1.5 shrink-0 gap-1">
        <button
          onClick={() => setActiveTab("mission")}
          className={`flex-1 py-2 rounded-lg font-mono text-[10px] font-bold tracking-wider transition-all flex items-center justify-center gap-2 ${
            activeTab === "mission"
              ? "bg-asta-green/10 text-asta-green border border-asta-green/25"
              : "text-gray-500 hover:text-gray-300 border border-transparent"
          }`}
        >
          <Swords className="h-3.5 w-3.5" />
          MISSION
        </button>
        <button
          onClick={() => setActiveTab("support")}
          className={`flex-1 py-2 rounded-lg font-mono text-[10px] font-bold tracking-wider transition-all flex items-center justify-center gap-2 ${
            activeTab === "support"
              ? "bg-asta-green/10 text-asta-green border border-asta-green/25"
              : "text-gray-500 hover:text-gray-300 border border-transparent"
          }`}
        >
          <BookOpen className="h-3.5 w-3.5" />
          SUPPORT
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {activeTab === "mission" ? (
          <>
            {/* Header */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="chip bg-asta-violet/10 text-asta-violet border-asta-violet/25">
                  DÉFI {level.level_index + 1}
                </span>
                <span className="text-[10px] text-gray-500 font-mono font-bold uppercase tracking-wider">
                  Fiche {level.difficulty}/10
                </span>
              </div>
              <h2 className="text-base font-display font-bold text-white leading-snug select-text">
                {level.title}
              </h2>

              {/* Meta chips */}
              <div className="flex flex-wrap gap-1.5">
                <span className="chip bg-ink-deep text-gray-400 border-ink-line gap-1">
                  <Clock className="h-3 w-3 text-asta-amber" />
                  {formatTime(level.time_limit)}
                </span>
                <span className="chip bg-ink-deep text-gray-400 border-ink-line gap-1">
                  <Trophy className="h-3 w-3 text-asta-green" />
                  {level.points} pts
                </span>
                <span className="chip bg-ink-deep text-gray-400 border-ink-line gap-1">
                  <Gauge className="h-3 w-3 text-asta-cyan" />
                  Difficulté {level.difficulty}
                </span>
              </div>
            </div>

            {/* Situation */}
            {level.situation_probleme && (
              <div className="space-y-2">
                <h3 className="section-title text-asta-violet">
                  <Compass className="h-4 w-4" />
                  Situation
                </h3>
                <div className="p-3.5 rounded-xl bg-ink-panel/70 border border-ink-line/70 text-gray-300 text-xs leading-relaxed select-text shadow-inset">
                  {renderMarkdown(level.situation_probleme)}
                </div>
              </div>
            )}

            {/* Consigne */}
            {level.consigne && (
              <div className="space-y-2">
                <h3 className="section-title text-asta-green">
                  <ListChecks className="h-4 w-4" />
                  Consigne d'exécution
                </h3>
                <div className="p-3.5 rounded-xl bg-asta-green/5 border border-asta-green/20 text-gray-200 text-xs leading-relaxed select-text space-y-1">
                  {renderMarkdown(level.consigne)}
                </div>
              </div>
            )}

            {/* Objective */}
            <div className="space-y-2">
              <h3 className="section-title">
                <Terminal className="h-4 w-4 text-asta-cyan" />
                Objectif
              </h3>
              <p className="text-xs text-gray-200 select-text leading-relaxed bg-ink-panel/70 border border-ink-line/70 rounded-xl p-3.5">
                {level.objective}
              </p>
            </div>

            {/* Validation criteria */}
            {checks.length > 0 && (
              <div className="space-y-2">
                <h3 className="section-title">
                  <ListChecks className="h-4 w-4 text-asta-cyan" />
                  Critères de validation
                </h3>
                <div className="space-y-1.5">
                  {checks.map((check, idx) => {
                    const details: string[] = [];
                    if (check.perms) details.push(`perms ${check.perms}`);
                    if (check.content_contains) details.push("contenu attendu");
                    if (check.content_not_contains) details.push("contenu à exclure");
                    return (
                      <div
                        key={idx}
                        className="flex items-start gap-2.5 p-2.5 rounded-lg bg-ink-panel/50 border border-ink-line/60"
                      >
                        <span className="h-5 w-5 rounded-md border border-ink-line2 bg-ink-deep flex items-center justify-center text-[9px] font-black text-gray-400 shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <div className="text-xs text-gray-300 select-text">
                          <code className="font-mono text-[11px] text-white">{check.path}</code>
                          {details.length > 0 && (
                            <span className="text-gray-500"> — {details.join(" · ")}</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Hints */}
            {level.hints?.length > 0 && (
              <div className="space-y-2">
                <h3 className="section-title text-asta-amber">
                  <Lightbulb className="h-4 w-4" />
                  Indices progressifs
                </h3>
                <div className="space-y-1.5">
                  {level.hints.map((hint, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg bg-asta-amber/5 border border-asta-amber/15 text-[11px] text-gray-300 leading-relaxed select-text">
                      <span className="font-mono font-bold text-asta-amber mr-1.5">[{idx + 1}]</span>
                      {hint}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <>
            <div className="space-y-2">
              <h3 className="section-title text-asta-green">
                <BookOpen className="h-4 w-4" />
                Support technique
              </h3>
              <p className="text-[11px] text-gray-500 leading-relaxed">
                Manuel adapté à ce défi. Lis-le avant de te lancer, puis garde-le sous
                les yeux pendant l'exécution.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-ink-panel/70 border border-ink-line/70 space-y-1 select-text">
              {renderMarkdown(level.support_technique) ?? (
                <p className="text-xs text-gray-400">Aucun support fourni pour ce défi.</p>
              )}
            </div>
            <div className="p-3 rounded-xl bg-asta-violet/5 border border-asta-violet/15 text-[11px] text-gray-400 leading-relaxed">
              <span className="font-bold text-asta-violet">Astuce :</span> le shell est réel. Tu peux utiliser{" "}
              <code className="text-asta-green font-mono">man</code>,{" "}
              <code className="text-asta-green font-mono">--help</code> et les tabulations pour explorer les
              commandes par toi-même.
            </div>
          </>
        )}
      </div>
    </div>
  );
}
